# app/modules/assistant/services/auth_service.py
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from app.core.config.settings import Configuration
import jwt
import bcrypt
from app.modules.users.models.user_models import User
from app.shared.database.connection import get_session
from app.modules.auth.schemas.auth import TokenData


class AuthService:
    """Serviço para autenticação"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.configuration = Configuration()
        self.secret_key = self.configuration.secret_key
        self.expiration_hours = self.configuration.auth_jwt_expiration
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Autentica um usuário pelo username e senha
        Retorna um dicionário com os dados do usuário
        """
        session = get_session()
        try:
            user = session.query(User).where(User.username == username).first()
            if not user:
                return None
            
            # Verifica se o usuário está ativo
            if not user.is_active:
                return None
            
            # Verifica a senha
            if bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
                # Atualiza o último login
                user.last_login = datetime.now()
                session.add(user)
                session.commit()
                
                # Retorna os dados como dicionário (NÃO retorna o objeto da sessão)
                return {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_admin": user.is_admin,
                    "is_active": user.is_active,
                    "password_hash": user.password_hash  # Mantém para gerar token
                }
            
            return None
        finally:
            session.close()
    
    def generate_jwt(self, user_data: Dict[str, Any]) -> str:
        """
        Gera um token JWT para o usuário
        """
        expiration = datetime.now(timezone.utc) + timedelta(hours=self.expiration_hours)
        payload = {
            "user_id": user_data["id"],
            "username": user_data["username"],
            "exp": expiration
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")
    
    def decode_jwt(self, token: str) -> Optional[TokenData]:
        """
        Decodifica e valida um token JWT
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return TokenData(
                user_id=payload.get("user_id"),
                username=payload.get("username"),
                exp=payload.get("exp")
            )
        except jwt.ExpiredSignatureError:
            self.logger.warning("Token expirado")
            return None
        except jwt.InvalidTokenError as e:
            self.logger.warning(f"Token inválido: {e}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Busca um usuário pelo ID e retorna como dicionário
        """
        session = get_session()
        try:
            user = session.get(User, user_id)
            if user:
                return {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_admin": user.is_admin,
                    "is_active": user.is_active,
                    "password_hash": user.password_hash
                }
            return None
        finally:
            session.close()