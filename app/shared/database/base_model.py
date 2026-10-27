# app/shared/database/base_model.py
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
import uuid


class BaseModel(SQLModel):
    """Modelo base com campos comuns"""
    id: Optional[int] = Field(default=None, primary_key=True)

    uuid: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        max_length=36,
        unique=True,
        index=True,
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None)