from typing import Optional

from pydantic import BaseModel


class AddItemRequest(BaseModel):
    description: str
    amount: float
    transaction_type: str
    category: str
    subcategory: Optional[str] = None
    reference_month: Optional[str] = None
    status: str = "pending"
    notes: Optional[str] = None


class UpdateItemRequest(BaseModel):
    description: Optional[str] = None
    amount: Optional[float] = None
    transaction_type: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    payment_date: Optional[str] = None
    due_date: Optional[str] = None
