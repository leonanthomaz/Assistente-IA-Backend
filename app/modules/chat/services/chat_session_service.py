# # app/modules/chat/services/chat_session_service.py
# import logging
# from typing import Dict, Optional, List
# from datetime import datetime

# from sqlmodel import select, desc

# from app.shared.database.connection import get_session

# from app.modules.chat.models.chat_models import Chat, ChatItem
# from app.modules.assistant.models.assistant_model import Assistant
# from app.modules.chat.services.chat_service import ChatService
# from app.shared.utils.retornar_timestamp import get_current_timestamp


# class ChatSessionService:
#     """
#     Orquestra o ciclo de vida de uma conversa:
#     - cria/recupera o Chat
#     - salva ChatItems (user e assistant)
#     - monta o histórico
#     - delega a chamada da IA pro ChatService
#     """

#     # Quantas mensagens anteriores mandar pro modelo
#     HISTORY_LIMIT = 20

#     def __init__(self):
#         self.logger = logging.getLogger(__name__)
#         self.chat_service = ChatService()

#     # ============ BUSCAR / CRIAR CHAT ============
#     def get_or_create_chat(
#         self,
#         user_id: int,
#         chat_id: Optional[int] = None,
#         title: Optional[str] = None,
#         context_type: str = "general",
#     ) -> Dict:
#         session = get_session()
#         try:
#             chat = None

#             if chat_id:
#                 chat = session.get(Chat, chat_id)
#                 if chat and chat.user_id != user_id:
#                     # proteção básica: chat de outro usuário
#                     chat = None

#             if not chat:
#                 # Pega o assistant padrão do usuário
#                 assistant = session.exec(
#                     select(Assistant).where(
#                         Assistant.user_id == user_id,
#                         Assistant.is_default == True,  # noqa: E712
#                         Assistant.is_active == True,   # noqa: E712
#                     )
#                 ).first()

#                 chat = Chat(
#                     master_id=assistant.master_id if assistant else 1,
#                     user_id=user_id,
#                     assistant_id=assistant.id if assistant else None,
#                     title=title or "Nova Conversa",
#                     context_type=context_type,
#                     status="active",
#                     total_messages=0,
#                     total_tokens=0,
#                 )
#                 session.add(chat)
#                 session.commit()
#                 session.refresh(chat)

#             return {
#                 "id": chat.id,
#                 "uuid": chat.uuid,
#                 "title": chat.title,
#                 "assistant_id": chat.assistant_id,
#                 "total_messages": chat.total_messages,
#                 "total_tokens": chat.total_tokens,
#             }
#         finally:
#             session.close()

#     # ============ HISTÓRICO ============
#     def get_history(self, chat_id: int, limit: int = None) -> List[Dict[str, str]]:
#         """
#         Retorna as últimas `limit` mensagens do chat, em ordem cronológica,
#         no formato aceito pela API da Groq: [{"role": ..., "content": ...}]
#         """
#         limit = limit or self.HISTORY_LIMIT
#         session = get_session()
#         try:
#             # pega as N últimas (desc), depois inverte
#             items = session.exec(
#                 select(ChatItem)
#                 .where(ChatItem.chat_id == chat_id)
#                 .order_by(desc(ChatItem.created_at))
#                 .limit(limit)
#             ).all()

#             items.reverse()

#             return [
#                 {"role": item.role, "content": item.content}
#                 for item in items
#                 if item.role in ("user", "assistant", "system")
#             ]
#         finally:
#             session.close()

#     # ============ SALVAR ITEM ============
#     def save_item(
#         self,
#         chat_id: int,
#         role: str,
#         content: str,
#         tokens_used: int = 0,
#         response_time: Optional[float] = None,
#         metadata_json: Optional[str] = None,
#     ) -> Dict:
#         session = get_session()
#         try:
#             item = ChatItem(
#                 chat_id=chat_id,
#                 role=role,
#                 content=content,
#                 tokens_used=tokens_used,
#                 response_time=response_time,
#                 metadata_json=metadata_json,
#             )
#             session.add(item)

#             # atualiza contadores do chat
#             chat = session.get(Chat, chat_id)
#             if chat:
#                 chat.total_messages += 1
#                 chat.total_tokens += tokens_used
#                 chat.updated_at = datetime.utcnow()
#                 session.add(chat)

#             session.commit()
#             session.refresh(item)

#             return {
#                 "id": item.id,
#                 "role": item.role,
#                 "content": item.content,
#                 "created_at": item.created_at.isoformat() if item.created_at else None,
#             }
#         finally:
#             session.close()

#     # ============ CICLO COMPLETO (TEXTO) ============
#     async def process_text_message(
#         self,
#         user_id: int,
#         message: str,
#         chat_id: Optional[int] = None,
#         model: Optional[str] = None,
#         temperature: float = 0.7,
#         max_tokens: int = 2048,
#     ) -> Dict:
#         # 1. Garante que existe um Chat
#         chat = self.get_or_create_chat(user_id, chat_id=chat_id)

#         # 2. Salva a mensagem do usuário
#         self.save_item(chat_id=chat["id"], role="user", content=message)

#         # 3. Monta o histórico (inclui a msg recém-salva)
#         history = self.get_history(chat["id"], limit=self.HISTORY_LIMIT)

#         # O histórico já termina com a mensagem atual.
#         # Vamos passar pro service apenas as mensagens ANTERIORES
#         # e mandar a mensagem atual separada (como o service espera).
#         history_without_last = history[:-1] if history else []

#         # 4. Chama a IA
#         result = await self.chat_service.generate_response(
#             message=message,
#             model=model,
#             temperature=temperature,
#             max_tokens=max_tokens,
#             history=history_without_last,
#         )

#         if not result.get("success"):
#             # mesmo em erro, o ChatItem do user já está salvo.
#             # Devolve o erro pro controller.
#             return {**result, "chat_id": chat["id"]}

#         # 5. Salva a resposta do assistant
#         usage = result.get("usage") or {}
#         self.save_item(
#             chat_id=chat["id"],
#             role="assistant",
#             content=result["response"],
#             tokens_used=usage.get("completion_tokens", 0),
#         )

#         return {
#             "success": True,
#             "chat_id": chat["id"],
#             "response": result["response"],
#             "model": result.get("model"),
#             "usage": usage,
#             "timestamp": get_current_timestamp(),
#         }

#     # ============ CICLO COMPLETO (VOZ) ============
#     async def process_voice_message(
#         self,
#         user_id: int,
#         audio_data: bytes,
#         chat_id: Optional[int] = None,
#         model: Optional[str] = None,
#         return_audio: bool = True,
#     ) -> Dict:
#         # 1. STT
#         success, user_text = self.chat_service.voice_service.speech_to_text(audio_data)
#         if not success:
#             return {
#                 "success": False,
#                 "message": user_text,
#                 "timestamp": get_current_timestamp(),
#             }

#         # 2. Garante o Chat
#         chat = self.get_or_create_chat(user_id, chat_id=chat_id)

#         # 3. Salva a mensagem do usuário (transcrita)
#         self.save_item(chat_id=chat["id"], role="user", content=user_text)

#         # 4. Histórico sem a última
#         history = self.get_history(chat["id"], limit=self.HISTORY_LIMIT)
#         history_without_last = history[:-1] if history else []

#         # 5. IA
#         result = await self.chat_service.generate_response(
#             message=user_text,
#             model=model,
#             history=history_without_last,
#         )

#         if not result.get("success"):
#             return {**result, "chat_id": chat["id"]}

#         assistant_text = result.get("response", "")

#         # 6. Salva resposta do assistant
#         usage = result.get("usage") or {}
#         self.save_item(
#             chat_id=chat["id"],
#             role="assistant",
#             content=assistant_text,
#             tokens_used=usage.get("completion_tokens", 0),
#         )

#         # 7. TTS (opcional)
#         audio_base64 = None
#         if return_audio and assistant_text:
#             audio_base64 = await self.chat_service.voice_service.text_to_speech(assistant_text)

#         return {
#             "success": True,
#             "chat_id": chat["id"],
#             "user_text": user_text,
#             "assistant_text": assistant_text,
#             "model": result.get("model"),
#             "usage": usage,
#             "audio": audio_base64,
#             "timestamp": get_current_timestamp(),
#         }

#     def ensure_chat(self, user_id: int, chat_id: Optional[int] = None) -> Dict:
#         """Garante que existe um chat. Se não, cria um vazio."""
#         return self.get_or_create_chat(user_id, chat_id=chat_id)
    
#     # ============ LISTAR CHATS DO USUÁRIO ============
#     def list_user_chats(self, user_id: int, limit: int = 20) -> List[Dict]:
#         session = get_session()
#         try:
#             chats = session.exec(
#                 select(Chat)
#                 .where(Chat.user_id == user_id, Chat.status == "active")
#                 .order_by(desc(Chat.updated_at))
#                 .limit(limit)
#             ).all()

#             return [
#                 {
#                     "id": c.id,
#                     "uuid": c.uuid,
#                     "title": c.title,
#                     "context_type": c.context_type,
#                     "total_messages": c.total_messages,
#                     "updated_at": c.updated_at.isoformat() if c.updated_at else None,
#                 }
#                 for c in chats
#             ]
#         finally:
#             session.close()