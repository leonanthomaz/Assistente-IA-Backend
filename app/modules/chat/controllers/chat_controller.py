# app/modules/chat/controllers/chat_controller.py
import logging
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends

from app.core.middleware.auth_dependencies import get_current_user_id
from app.core.middleware.validate_api_key import validate_internal_api_key
from app.modules.assistant.models.groq_model import GroqChatRequest
from app.modules.chat.services.chat_service import ChatService
from app.shared.utils.retornar_timestamp import get_current_timestamp


class ChatController(APIRouter):
    def __init__(self):
        super().__init__(
            dependencies=[Depends(validate_internal_api_key)],
        )
        self.logger = logging.getLogger(__name__)
        self.chat_service = ChatService()

        self.add_api_route("/health", self.health_check, methods=["GET"], summary="Health check")
        self.add_api_route("/chat", self.chat, methods=["POST"], summary="Conversa por texto")
        self.add_api_route("/chat/voice", self.chat_voice, methods=["POST"], summary="Conversa por voz")
        self.add_api_route("/chats", self.list_chats, methods=["GET"], summary="Lista conversas")
        self.add_api_route("/chats/current", self.get_current_chat, methods=["GET"], summary="Chat atual")
        self.add_api_route("/chats/{chat_id}/history", self.get_history, methods=["GET"], summary="Histórico")
        self.add_api_route("/models", self.list_models, methods=["GET"], summary="Lista modelos")

    # ============ HANDLERS ============
    def health_check(self) -> Dict[str, str]:
        return {"status": "ONLINE", "service": "API CHAT", "timestamp": get_current_timestamp()}

    async def chat(
        self,
        request: GroqChatRequest,
        user_id: int = Depends(get_current_user_id),
    ) -> Dict:
        try:
            result = await self.chat_service.process_text_message(
                user_id=user_id,
                message=request.message,
                chat_id=getattr(request, "chat_id", None),
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )
            if not result.get("success"):
                status = 504 if result.get("error") == "timeout" else 502
                raise HTTPException(status_code=status, detail=result.get("message", "Erro"))
            return result
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Erro no chat: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def chat_voice(
        self,
        file: UploadFile = File(..., description="WAV"),
        model: Optional[str] = Form(None),
        return_audio: bool = Form(True),
        chat_id: Optional[int] = Form(None),
        user_id: int = Depends(get_current_user_id),
    ) -> Dict:
        try:
            if not file.content_type or "wav" not in file.content_type.lower():
                raise HTTPException(status_code=400, detail="Envie um WAV")
            audio_data = await file.read()

            result = await self.chat_service.process_voice_message(
                user_id=user_id,
                audio_data=audio_data,
                chat_id=chat_id,
                model=model,
                return_audio=return_audio,
            )
            if not result.get("success"):
                raise HTTPException(status_code=502, detail=result.get("message", "Erro"))
            return result
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Erro no chat_voice: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def list_chats(self, user_id: int = Depends(get_current_user_id)) -> Dict:
        return self.chat_service.list_chats(user_id)

    async def get_current_chat(self, user_id: int = Depends(get_current_user_id)) -> Dict:
        return self.chat_service.get_current_chat(user_id)

    async def get_history(
        self,
        chat_id: int,
        user_id: int = Depends(get_current_user_id),
    ) -> Dict:
        result = self.chat_service.get_history(user_id, chat_id)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("message", "Não encontrado"))
        return result

    async def list_models(self) -> Dict:
        result = await self.chat_service.list_models()
        if not result.get("success"):
            raise HTTPException(status_code=502, detail=result.get("message", "Erro"))
        return result