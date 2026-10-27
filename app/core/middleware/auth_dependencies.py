# app/core/dependencies/auth_dependencies.py
from typing import Optional
from fastapi import Header, Depends, status

from app.core.exceptions.auth_exception import AuthException
from app.modules.auth.services.auth_service import AuthService

auth_service = AuthService()


def get_current_user_id(authorization: Optional[str] = Header(None)) -> int:
    if not authorization:
        raise AuthException(status.HTTP_401_UNAUTHORIZED, "Acesso não autorizado")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthException(status.HTTP_401_UNAUTHORIZED, "Formato inválido")

    token_data = auth_service.decode_jwt(parts[1])
    if not token_data:
        raise AuthException(status.HTTP_401_UNAUTHORIZED, "Token inválido ou expirado")

    return token_data.user_id