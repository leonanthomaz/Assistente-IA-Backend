# app/modules/chat/repositories/chat_repository.py
from typing import Optional, List
from datetime import datetime
from sqlmodel import select, desc

from app.shared.database.connection import get_session
from app.modules.chat.models.chat_models import Chat, ChatItem
from app.modules.assistant.models.assistant_model import Assistant


class ChatRepository:
    """Comunicação com o banco para chats."""

    def get_user_assistant(self, user_id: int) -> Optional[Assistant]:
        session = get_session()
        try:
            return session.exec(
                select(Assistant).where(
                    Assistant.user_id == user_id,
                    Assistant.is_default == True,  # noqa: E712
                    Assistant.is_active == True,   # noqa: E712
                )
            ).first()
        finally:
            session.close()

    def get_chat(self, chat_id: int, user_id: int) -> Optional[Chat]:
        session = get_session()
        try:
            chat = session.get(Chat, chat_id)
            if chat and chat.user_id == user_id:
                return chat
            return None
        finally:
            session.close()

    def get_latest_active_chat(self, user_id: int) -> Optional[Chat]:
        session = get_session()
        try:
            return session.exec(
                select(Chat)
                .where(Chat.user_id == user_id, Chat.status == "active")
                .order_by(desc(Chat.updated_at))
                .limit(1)
            ).first()
        finally:
            session.close()

    def create_chat(
        self,
        user_id: int,
        assistant_id: Optional[int] = None,
        title: str = "Nova Conversa",
        context_type: str = "general",
    ) -> Chat:
        session = get_session()
        try:
            chat = Chat(
                user_id=user_id,
                assistant_id=assistant_id,
                title=title,
                context_type=context_type,
                status="active",
                total_messages=0,
                total_tokens=0,
            )
            session.add(chat)
            session.commit()
            session.refresh(chat)
            return chat
        finally:
            session.close()

    def list_user_chats(self, user_id: int, limit: int = 20) -> List[Chat]:
        session = get_session()
        try:
            return list(
                session.exec(
                    select(Chat)
                    .where(Chat.user_id == user_id, Chat.status == "active")
                    .order_by(desc(Chat.updated_at))
                    .limit(limit)
                ).all()
            )
        finally:
            session.close()

    def get_history(self, chat_id: int, limit: int = 20) -> List[ChatItem]:
        session = get_session()
        try:
            items = session.exec(
                select(ChatItem)
                .where(ChatItem.chat_id == chat_id)
                .order_by(desc(ChatItem.created_at))
                .limit(limit)
            ).all()
            items = list(items)
            items.reverse()
            return items
        finally:
            session.close()

    def save_item(
        self,
        chat_id: int,
        role: str,
        content: str,
        tokens_used: int = 0,
    ) -> ChatItem:
        session = get_session()
        try:
            item = ChatItem(
                chat_id=chat_id,
                role=role,
                content=content,
                tokens_used=tokens_used,
            )
            session.add(item)

            chat = session.get(Chat, chat_id)
            if chat:
                chat.total_messages += 1
                chat.total_tokens += tokens_used
                chat.updated_at = datetime.utcnow()
                session.add(chat)

            session.commit()
            session.refresh(item)
            return item
        finally:
            session.close()