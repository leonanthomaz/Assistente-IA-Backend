# app/modules/chat/services/chat_service.py
import logging
import httpx
from typing import Dict, Optional, List, Any

from app.core.config.settings import Configuration
from app.modules.assistant.services.voice_service import VoiceService
from app.modules.assistant.services.assistant_service import AssistantService
from app.modules.chat.repositories.chat_repository import ChatRepository
from app.modules.users.repositories.user_repository import UserRepository
from app.modules.context import tools  # noqa: F401  → dispara o registro das tools
from app.modules.context.registry import list_schemas as list_tool_schemas
from app.modules.context.executor import ToolExecutor
from app.shared.utils.retornar_timestamp import get_current_timestamp


FALLBACK_PERSONA = "You are a helpful assistant. Always respond in Portuguese."


class ChatService:
    """Regras de negócio do chat com tool calling."""

    HISTORY_LIMIT = 20
    MAX_TOOL_ITERATIONS = 3

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = Configuration()
        self.voice_service = VoiceService()
        self.repository = ChatRepository()
        self.assistant_service = AssistantService()
        self.user_repository = UserRepository()
        self.tool_executor = ToolExecutor()

    # ============ RESOLUÇÃO DE CHAT ============
    def _resolve_chat(self, user_id: int, chat_id: Optional[int]):
        if chat_id:
            chat = self.repository.get_chat(chat_id, user_id)
            if chat:
                return chat

        chat = self.repository.get_latest_active_chat(user_id)
        if chat:
            return chat

        assistant = self.repository.get_user_assistant(user_id)
        return self.repository.create_chat(
            user_id=user_id,
            assistant_id=assistant.id if assistant else None,
        )

    def _chat_to_dict(self, chat) -> Dict:
        return {
            "id": chat.id,
            "uuid": chat.uuid,
            "title": chat.title,
            "assistant_id": chat.assistant_id,
            "total_messages": chat.total_messages,
            "total_tokens": chat.total_tokens,
        }

    def _items_to_history(self, items) -> List[Dict[str, str]]:
        return [
            {"role": i.role, "content": i.content}
            for i in items
            if i.role in ("user", "assistant", "system")
        ]

    # ============ CONTEXTO ============
    def _build_persona(self, assistant) -> str:
        """Persona vem sempre do assistant do banco. Fallback neutro se vazio."""
        if assistant and assistant.system_prompt:
            return assistant.system_prompt
        return FALLBACK_PERSONA

    def _build_base_context(self, user_id: int, assistant) -> str:
        """Contexto base: quem é o user e o assistant."""
        user = self.user_repository.get_by_id(user_id)

        lines = ["Contexto atual:"]
        if user:
            lines.append(f"- Usuário: {user.full_name}")
        if assistant:
            lines.append(f"- Assistente: {assistant.name}")
            if assistant.personality:
                lines.append(f"- Personalidade: {assistant.personality}")
            if assistant.communication_style:
                lines.append(f"- Estilo: {assistant.communication_style}")
        lines.append(f"- Data/hora: {get_current_timestamp()}")
        return "\n".join(lines)

    # ============ CHAMADA À IA ============
    async def _call_groq(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float,
        max_tokens: int,
        tools: Optional[List[Dict]] = None,
    ) -> Dict:
        api_key = self.config.groq_api_key
        url = self.config.groq_url or "https://api.groq.com/openai/v1/chat/completions"

        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()

            choice = data.get("choices", [{}])[0]
            msg = choice.get("message", {}) or {}
            usage = data.get("usage", {})

            return {
                "success": True,
                "content": msg.get("content"),
                "tool_calls": msg.get("tool_calls"),
                "model": model,
                "usage": {
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                },
            }
        except httpx.TimeoutException:
            return {"success": False, "error": "timeout", "message": "Tempo limite excedido."}
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json().get("error", {}).get("message", str(e))
            except Exception:
                detail = e.response.text
            return {"success": False, "error": "http_error", "message": f"Erro Groq: {detail}"}
        except Exception as e:
            self.logger.error(f"Erro inesperado na IA: {e}")
            return {"success": False, "error": "unexpected", "message": str(e)}

    async def _generate_with_tools(
        self,
        user_id: int,
        message: str,
        assistant,
        history: List[Dict[str, str]],
        model: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> Dict:
        """Loop de tool calling. Retorna resposta final + usage acumulado."""
        effective_model = (
            model
            or (assistant.model if assistant else None)
            or self.config.groq_model
            or "openai/gpt-oss-20b"
        )
        effective_temp = temperature if temperature is not None else (assistant.temperature if assistant else 0.7)
        effective_max = max_tokens or (assistant.max_tokens if assistant else 2048)

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": self._build_persona(assistant)},
            {"role": "system", "content": self._build_base_context(user_id, assistant)},
        ]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": message})

        tool_schemas = list_tool_schemas()
        total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        for iteration in range(self.MAX_TOOL_ITERATIONS):
            result = await self._call_groq(
                messages=messages,
                model=effective_model,
                temperature=effective_temp,
                max_tokens=effective_max,
                tools=tool_schemas,
            )

            if not result.get("success"):
                return result

            u = result.get("usage") or {}
            for k in total_usage:
                total_usage[k] += u.get(k, 0)

            tool_calls = result.get("tool_calls")
            content = result.get("content")

            if not tool_calls:
                return {
                    "success": True,
                    "response": content or "",
                    "model": effective_model,
                    "usage": total_usage,
                }

            messages.append({
                "role": "assistant",
                "content": content,
                "tool_calls": tool_calls,
            })

            self.logger.info(
                f"Tool calls (iter {iteration + 1}): "
                f"{[tc.get('function', {}).get('name') for tc in tool_calls]}"
            )
            tool_messages = self.tool_executor.execute(tool_calls, user_id=user_id)
            messages.extend(tool_messages)

        return {
            "success": False,
            "error": "max_iterations",
            "message": "A IA excedeu o número de chamadas de ferramenta.",
        }

    # ============ CASOS DE USO ============
    def get_current_chat(self, user_id: int) -> Dict:
        chat = self._resolve_chat(user_id, chat_id=None)
        items = self.repository.get_history(chat.id, limit=100)
        return {
            "success": True,
            "chat": self._chat_to_dict(chat),
            "messages": self._items_to_history(items),
            "timestamp": get_current_timestamp(),
        }

    def list_chats(self, user_id: int) -> Dict:
        chats = self.repository.list_user_chats(user_id)
        return {
            "success": True,
            "total": len(chats),
            "chats": [self._chat_to_dict(c) for c in chats],
            "timestamp": get_current_timestamp(),
        }

    def get_history(self, user_id: int, chat_id: int) -> Dict:
        chat = self.repository.get_chat(chat_id, user_id)
        if not chat:
            return {"success": False, "error": "not_found", "message": "Chat não encontrado"}

        items = self.repository.get_history(chat_id, limit=100)
        return {
            "success": True,
            "chat_id": chat_id,
            "messages": self._items_to_history(items),
            "timestamp": get_current_timestamp(),
        }

    async def process_text_message(
        self,
        user_id: int,
        message: str,
        chat_id: Optional[int] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Dict:
        chat = self._resolve_chat(user_id, chat_id=chat_id)
        assistant = self.assistant_service.get_assistant_by_user(user_id)

        items = self.repository.get_history(chat.id, limit=self.HISTORY_LIMIT)
        history = self._items_to_history(items)

        result = await self._generate_with_tools(
            user_id=user_id,
            message=message,
            assistant=assistant,
            history=history,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        if not result.get("success"):
            return {**result, "chat_id": chat.id}

        self.repository.save_item(chat_id=chat.id, role="user", content=message)
        usage = result.get("usage") or {}
        self.repository.save_item(
            chat_id=chat.id,
            role="assistant",
            content=result["response"],
            tokens_used=usage.get("completion_tokens", 0),
        )

        return {
            "success": True,
            "chat_id": chat.id,
            "response": result["response"],
            "model": result.get("model"),
            "usage": usage,
            "timestamp": get_current_timestamp(),
        }

    async def process_voice_message(
        self,
        user_id: int,
        audio_data: bytes,
        chat_id: Optional[int] = None,
        model: Optional[str] = None,
        return_audio: bool = True,
    ) -> Dict:
        success, user_text = self.voice_service.speech_to_text(audio_data)
        if not success:
            return {"success": False, "message": user_text, "timestamp": get_current_timestamp()}

        chat = self._resolve_chat(user_id, chat_id=chat_id)
        assistant = self.assistant_service.get_assistant_by_user(user_id)

        items = self.repository.get_history(chat.id, limit=self.HISTORY_LIMIT)
        history = self._items_to_history(items)

        result = await self._generate_with_tools(
            user_id=user_id,
            message=user_text,
            assistant=assistant,
            history=history,
            model=model,
            temperature=0.7,
            max_tokens=2048,
        )

        if not result.get("success"):
            return {**result, "chat_id": chat.id}

        assistant_text = result.get("response", "")
        usage = result.get("usage") or {}

        self.repository.save_item(chat_id=chat.id, role="user", content=user_text)
        self.repository.save_item(
            chat_id=chat.id,
            role="assistant",
            content=assistant_text,
            tokens_used=usage.get("completion_tokens", 0),
        )

        audio_base64 = None
        if return_audio and assistant_text:
            audio_base64 = await self.voice_service.text_to_speech(assistant_text)

        return {
            "success": True,
            "chat_id": chat.id,
            "user_text": user_text,
            "assistant_text": assistant_text,
            "model": result.get("model"),
            "usage": usage,
            "audio": audio_base64,
            "timestamp": get_current_timestamp(),
        }

    async def list_models(self) -> Dict:
        api_key = self.config.groq_api_key
        url = "https://api.groq.com/openai/v1/models"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()

            models = [
                {"id": m.get("id", ""), "created": m.get("created"), "owned_by": m.get("owned_by", "groq")}
                for m in data.get("data", [])
                if any(k in m.get("id", "") for k in ["llama", "gpt-oss", "qwen", "whisper"])
            ]
            return {"success": True, "total_models": len(models), "models": models, "timestamp": get_current_timestamp()}
        except Exception as e:
            return {"success": False, "error": "unexpected", "message": str(e), "timestamp": get_current_timestamp()}