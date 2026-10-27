# app/modules/users/controllers/user_controller.py

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from app.core.config.settings import Configuration
from app.shared.utils.retornar_timestamp import get_current_timestamp
from app.modules.users.services.user_service import UserService

class UserController(APIRouter):
    """Controller para operações com Usuários"""
    
    def __init__(self):
        super().__init__()
        self.config = Configuration()
        self.logger = logging.getLogger(__name__)
        self.service = UserService()

        # Health check
        self.add_api_route(
            path="/health",
            endpoint=self.health_check,
            methods=["GET"],
            summary="Health check"
        )
        
        # ============ USER ENDPOINTS ============
        self.add_api_route(
            path="",
            endpoint=self.get_users,
            methods=["GET"],
            summary="Lista todos os usuários"
        )
        
        self.add_api_route(
            path="",
            endpoint=self.create_user,
            methods=["POST"],
            summary="Cria um novo usuário"
        )
        
        self.add_api_route(
            path="/{user_id}",
            endpoint=self.get_user,
            methods=["GET"],
            summary="Obtém usuário por ID"
        )
        
        self.add_api_route(
            path="/{user_id}",
            endpoint=self.update_user,
            methods=["PUT"],
            summary="Atualiza um usuário"
        )
        
        self.add_api_route(
            path="/{user_id}",
            endpoint=self.delete_user,
            methods=["DELETE"],
            summary="Deleta/Desativa um usuário"
        )
        
    
    # ============ HEALTH ============
    def health_check(self) -> Dict[str, str]:
        return {
            "status": "ONLINE",
            "service": "API USER",
            "timestamp": get_current_timestamp()
        }
    
    # ============ USER METHODS ============
    async def get_users(self, active_only: bool = True) -> Dict:
        """Lista todos os usuários"""
        try:
            users = self.service.get_all_users(active_only)
            return {
                "success": True,
                "total": len(users),
                "data": [
                    {
                        "id": u.id,
                        "username": u.username,
                        "email": u.email,
                        "full_name": u.full_name,
                        "is_active": u.is_active,
                        "is_admin": u.is_admin,
                        "created_at": u.created_at.isoformat() if u.created_at else None
                    } for u in users
                ]
            }
        except Exception as e:
            self.logger.error(f"Erro ao listar usuários: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict:
        """Cria um novo usuário"""
        try:
            user = self.service.create_user(
                username=user_data.get('username'),
                email=user_data.get('email'),
                full_name=user_data.get('full_name'),
                **{k: v for k, v in user_data.items() if k not in ['username', 'email', 'full_name']}
            )
            return {
                "success": True,
                "message": "Usuário criado com sucesso",
                "data": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name
                }
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            self.logger.error(f"Erro ao criar usuário: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_user(self, user_id: int) -> Dict:
        """Obtém usuário por ID"""
        try:
            user = self.service.get_user_by_id(user_id)
            if user:
                return {
                    "success": True,
                    "data": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "full_name": user.full_name,
                        "preferred_language": user.preferred_language,
                        "timezone": user.timezone,
                        "is_active": user.is_active,
                        "is_admin": user.is_admin,
                        "bio": user.bio,
                        "created_at": user.created_at.isoformat() if user.created_at else None,
                        "updated_at": user.updated_at.isoformat() if user.updated_at else None
                    }
                }
            return {"success": False, "message": "Usuário não encontrado"}
        except Exception as e:
            self.logger.error(f"Erro ao obter usuário: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def update_user(self, user_id: int, user_data: Dict[str, Any]) -> Dict:
        """Atualiza um usuário"""
        try:
            user = self.service.update_user(user_id, **user_data)
            if user:
                return {
                    "success": True,
                    "message": "Usuário atualizado com sucesso",
                    "data": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "full_name": user.full_name
                    }
                }
            return {"success": False, "message": "Usuário não encontrado"}
        except Exception as e:
            self.logger.error(f"Erro ao atualizar usuário: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def delete_user(self, user_id: int, soft: bool = True) -> Dict:
        """Deleta/Desativa um usuário"""
        try:
            result = self.service.delete_user(user_id, soft_delete=soft)
            if result:
                return {
                    "success": True,
                    "message": f"Usuário {'desativado' if soft else 'deletado'} com sucesso"
                }
            return {"success": False, "message": "Usuário não encontrado"}
        except Exception as e:
            self.logger.error(f"Erro ao deletar usuário: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    