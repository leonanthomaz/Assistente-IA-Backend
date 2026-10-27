# app/modules/finance/models/finance_models.py
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from sqlmodel import Field, Relationship

from app.shared.database.base_model import BaseModel

if TYPE_CHECKING:
    from app.modules.master.models.master_models import Master
    from app.modules.users.models.user_models import User


class Finance(BaseModel, table=True):
    """Tabela mestre de finanças"""
    __tablename__ = "tb_finances"

    master_id: int = Field(foreign_key="tb_master.id", index=True)
    user_id: int = Field(foreign_key="tb_users.id", index=True)

    reference_month: str = Field(max_length=7)
    reference_year: int = Field()

    total_income: float = Field(default=0.0)
    total_expenses: float = Field(default=0.0)
    total_balance: float = Field(default=0.0)
    
    is_closed: bool = Field(default=False)
    closed_at: Optional[datetime] = Field(default=None)

    # Relacionamentos
    user: "User" = Relationship(back_populates="finances")
    items: List["FinanceItem"] = Relationship(back_populates="finance")


class FinanceItem(BaseModel, table=True):
    """Tabela de items/transações financeiras"""
    __tablename__ = "tb_finance_items"

    finance_id: int = Field(foreign_key="tb_finances.id", index=True)

    description: str = Field(max_length=500)
    amount: float = Field()
    transaction_type: str = Field(max_length=20)
    category: str = Field(max_length=100)
    subcategory: Optional[str] = Field(default=None, max_length=100)

    transaction_date: datetime = Field(default_factory=datetime.utcnow)
    due_date: Optional[datetime] = Field(default=None)
    payment_date: Optional[datetime] = Field(default=None)

    payment_method: Optional[str] = Field(default=None, max_length=50)
    status: str = Field(default="pending", max_length=20)

    is_recurring: bool = Field(default=False)
    recurring_period: Optional[str] = Field(default=None, max_length=20)
    recurring_end_date: Optional[datetime] = Field(default=None)

    notes: Optional[str] = Field(default=None)
    tags: Optional[str] = Field(default=None, max_length=500)
    attachments: Optional[str] = Field(default=None)

    # Relacionamentos
    finance: "Finance" = Relationship(back_populates="items")