from pydantic import BaseModel, Field
from typing import Dict, List, Optional

class GroqChatRequest(BaseModel):
    message: str
    model: Optional[str] = None
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=1024, ge=1, le=8192)
    stream: Optional[bool] = False
    chat_id: Optional[int] = None             # NOVO
    history: Optional[List[Dict[str, str]]] = None