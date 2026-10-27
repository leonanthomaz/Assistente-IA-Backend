# app/modules/chat/models/chat_models.py
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import Field, Relationship

from app.shared.database.base_model import BaseModel

if TYPE_CHECKING:
    from app.modules.master.models.master_models import Master
    from app.modules.users.models.user_models import User
    from app.modules.assistant.models.assistant_model import Assistant


class Chat(BaseModel, table=True):
    """Tabela de conversas/chats"""
    __tablename__ = "tb_chat"

    user_id: int = Field(foreign_key="tb_users.id", index=True)
    assistant_id: Optional[int] = Field(
        default=None,
        foreign_key="tb_assistants.id",
        index=True,
    )

    title: str = Field(max_length=200, default="Nova Conversa")
    context_type: str = Field(max_length=50, default="general")
    status: str = Field(max_length=20, default="active")

    total_messages: int = Field(default=0)
    total_tokens: int = Field(default=0)

    # Relacionamentos
    user: "User" = Relationship(back_populates="chats")
    assistant: Optional["Assistant"] = Relationship()
    items: List["ChatItem"] = Relationship(back_populates="chat", cascade_delete=True)


class ChatItem(BaseModel, table=True):
    """Tabela de mensagens/items de um chat"""
    __tablename__ = "tb_chat_items"

    chat_id: int = Field(foreign_key="tb_chat.id", index=True)

    role: str = Field(max_length=20)
    content: str = Field()

    tokens_used: Optional[int] = Field(default=0)
    response_time: Optional[float] = Field(default=None)

    metadata_json: Optional[str] = Field(default=None)

    # Relacionamentos
    chat: "Chat" = Relationship(back_populates="items")