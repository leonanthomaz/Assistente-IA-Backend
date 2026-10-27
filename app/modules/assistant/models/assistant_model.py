# app/modules/assistant/models/assistant_model.py
from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship

from app.shared.database.base_model import BaseModel

if TYPE_CHECKING:
    from app.modules.users.models.user_models import User


class Assistant(BaseModel, table=True):
    """Tabela de configurações da assistente"""
    __tablename__ = "tb_assistants"

    user_id: int = Field(foreign_key="tb_users.id", index=True)

    name: str = Field(max_length=100, default="Assistant")

    model: str = Field(max_length=100, default="openai/gpt-oss-20b")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048)

    greeting_message: Optional[str] = Field(
        default="Olá! Sou sua assistente pessoal. Como posso ajudar você hoje?",
        max_length=500,
    )
    system_prompt: Optional[str] = Field(
        default="You are a helpful assistant.",
        max_length=2000,
    )

    voice_provider: Optional[str] = Field(default=None, max_length=50)
    voice_id: Optional[str] = Field(default=None, max_length=100)
    voice_speed: Optional[float] = Field(default=1.0, ge=0.0, le=2.0)
    voice_pitch: Optional[float] = Field(default=1.0, ge=0.0, le=2.0)

    personality: Optional[str] = Field(default=None, max_length=50)
    communication_style: Optional[str] = Field(default=None, max_length=50)

    is_active: bool = Field(default=True)
    is_default: bool = Field(default=False)

    # Relacionamentos
    user: "User" = Relationship(back_populates="assistants")