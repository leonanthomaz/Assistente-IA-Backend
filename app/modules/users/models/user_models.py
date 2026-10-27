# app/modules/users/models/user_models.py
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from sqlmodel import Field, Relationship

from app.shared.database.base_model import BaseModel

if TYPE_CHECKING:
    from app.modules.master.models.master_models import Master
    from app.modules.assistant.models.assistant_model import Assistant
    from app.modules.chat.models.chat_models import Chat
    from app.modules.finance.models.finance_models import Finance


class User(BaseModel, table=True):
    """Tabela de usuários do sistema"""
    __tablename__ = "tb_users"

    master_id: int = Field(foreign_key="tb_master.id", index=True)

    username: str = Field(max_length=50, unique=True, index=True)
    email: str = Field(max_length=100, unique=True, index=True)
    full_name: str = Field(max_length=200)
    password_hash: str = Field(max_length=255)
    
    is_active: bool = Field(default=True)
    is_admin: bool = Field(default=False)
    last_login: Optional[datetime] = Field(default=None)

    preferred_language: str = Field(max_length=10, default="pt-BR")
    timezone: str = Field(max_length=50, default="America/Sao_Paulo")

    avatar_url: Optional[str] = Field(default=None, max_length=500)
    
    bio: Optional[str] = Field(default=None, max_length=500)
    occupation: Optional[str] = Field(default=None, max_length=100)  # "Desenvolvedor de software"
    interests: Optional[str] = Field(default=None, max_length=500)        # JSON: ["finanças", "musica", "games"]
    tone_preference: Optional[str] = Field(default=None, max_length=50)  # "formal" | "casual" | "sarcastico"

    # Relacionamentos
    master: "Master" = Relationship(back_populates="users")
    assistants: List["Assistant"] = Relationship(back_populates="user")
    chats: List["Chat"] = Relationship(back_populates="user")
    finances: List["Finance"] = Relationship(back_populates="user")