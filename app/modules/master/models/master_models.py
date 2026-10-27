# app/modules/master/models/master_models.py
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import Field, Relationship

from app.shared.database.base_model import BaseModel

if TYPE_CHECKING:
    from app.modules.users.models.user_models import User


class Master(BaseModel, table=True):
    """Tabela principal do sistema (Core)"""
    __tablename__ = "tb_master"

    system_name: str = Field(max_length=100, default="Assistant System")
    system_version: str = Field(max_length=20, default="1.0.0")
    is_active: bool = Field(default=True)
    maintenance_mode: bool = Field(default=False)

    default_language: str = Field(max_length=10, default="pt-BR")
    default_timezone: str = Field(max_length=50, default="America/Sao_Paulo")

    description: Optional[str] = Field(default=None, max_length=500)
    system_owner: Optional[str] = Field(default=None, max_length=100)

    # Relacionamentos — só o que existe do outro lado
    users: List["User"] = Relationship(back_populates="master")