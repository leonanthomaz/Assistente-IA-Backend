# app/modulos/assistente/schemas/auth.py
from typing import Optional
from pydantic import BaseModel, Field


class AuthCredentials(BaseModel):
    """Credenciais de login"""
    username: str = Field(..., description="Nome de usuário")
    password: str = Field(..., description="Senha do usuário")


class Token(BaseModel):
    """Token JWT"""
    access_token: str = Field(..., description="Token JWT")
    token_type: str = Field(default="bearer", description="Tipo do token")
    expires_in: int = Field(..., description="Tempo de expiração em segundos")


class TokenData(BaseModel):
    """Dados do token JWT"""
    user_id: int
    username: str
    exp: Optional[int] = None


class UserResponse(BaseModel):
    """Resposta com dados do usuário"""
    id: int
    username: str
    email: str
    full_name: str
    is_admin: bool
    is_active: bool