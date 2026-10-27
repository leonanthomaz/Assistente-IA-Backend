# app/modules/assistant/controllers/auth_controller.py
import logging
from typing import Dict
from fastapi import APIRouter, HTTPException, Header, status
from app.modules.auth.schemas.auth import AuthCredentials, Token, UserResponse
from app.modules.auth.services.auth_service import AuthService
from app.shared.utils.retornar_timestamp import get_current_timestamp


class AuthController(APIRouter):
    """Controller para autenticação"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.auth_service = AuthService()
        
        # Rotas de autenticação
        self.add_api_route(
            path="/login",
            endpoint=self.login,
            methods=["POST"],
            summary="Login do usuário",
            response_model=Token
        )
        
        self.add_api_route(
            path="/me",
            endpoint=self.me,
            methods=["GET"],
            summary="Obtém dados do usuário atual",
            response_model=UserResponse
        )
        
        self.add_api_route(
            path="/logout",
            endpoint=self.logout,
            methods=["POST"],
            summary="Logout (invalida o token)"
        )
        
        self.add_api_route(
            path="/refresh",
            endpoint=self.refresh_token,
            methods=["POST"],
            summary="Renova o token JWT"
        )
    
    def get_current_user(self, authorization: str = Header(None)) -> Dict:
        """
        Obtém o usuário atual a partir do token JWT
        """
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Acesso não autorizado"
            )
        
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Formato de autenticação inválido. Use: Bearer <token>"
            )
        
        token = parts[1]
        token_data = self.auth_service.decode_jwt(token)
        
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido ou expirado"
            )
        
        user = self.auth_service.get_user_by_id(token_data.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        if not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário desativado"
            )
        
        return user
    
    async def login(self, credentials: AuthCredentials) -> Token:
        """
        Realiza o login do usuário
        """
        try:
            user = self.auth_service.authenticate_user(
                credentials.username,
                credentials.password
            )
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Credenciais inválidas"
                )
            
            # Gera o token
            access_token = self.auth_service.generate_jwt(user)
            
            return Token(
                access_token=access_token,
                token_type="bearer",
                expires_in=self.auth_service.expiration_hours * 3600
            )
        
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Erro no login: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao realizar login"
            )
    
    async def me(self, authorization: str = Header(None)) -> UserResponse:
        """
        Retorna os dados do usuário atual
        """
        user_data = self.get_current_user(authorization)
        return UserResponse(**user_data)
    
    async def logout(self, authorization: str = Header(None)) -> Dict:
        """
        Realiza o logout (invalida o token)
        """
        self.get_current_user(authorization)
        
        return {
            "success": True,
            "message": "Logout realizado com sucesso",
            "timestamp": get_current_timestamp()
        }
    
    async def refresh_token(self, authorization: str = Header(None)) -> Token:
        """
        Renova o token JWT
        """
        user_data = self.get_current_user(authorization)
        
        # Gera novo token
        access_token = self.auth_service.generate_jwt(user_data)
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=self.auth_service.expiration_hours * 3600
        )