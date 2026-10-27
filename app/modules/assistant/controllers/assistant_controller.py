# app/modules/assistant/controller/assistant_controller.py
import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException

from app.core.config.settings import Configuration
from app.modules.assistant.services.assistant_service import AssistantService
from app.shared.utils.retornar_timestamp import get_current_timestamp


class AssistantController(APIRouter):
    """Controller para operações com Assistant."""

    def __init__(self):
        super().__init__()
        self.config = Configuration()
        self.logger = logging.getLogger(__name__)
        self.service = AssistantService()

        self.add_api_route("/health", self.health_check, methods=["GET"], summary="Health check")
        self.add_api_route("/", self.get_assistants, methods=["GET"], summary="Lista assistentes")
        self.add_api_route("/", self.create_assistant, methods=["POST"], summary="Cria assistente")
        self.add_api_route("/default", self.get_default_assistant, methods=["GET"], summary="Assistente padrão")
        self.add_api_route("/user/{user_id}", self.get_assistant_by_user, methods=["GET"], summary="Assistente do usuário")
        self.add_api_route("/{assistant_id}", self.get_assistant_by_id, methods=["GET"], summary="Assistente por ID")
        self.add_api_route("/{assistant_id}", self.update_assistant, methods=["PUT"], summary="Atualiza assistente")
        self.add_api_route("/{assistant_id}", self.delete_assistant, methods=["DELETE"], summary="Desativa assistente")
        self.add_api_route("/{assistant_id}/set-default", self.set_default_assistant, methods=["POST"], summary="Define como padrão")

    def health_check(self) -> Dict[str, str]:
        return {
            "status": "ONLINE",
            "service": "API ASSISTANT",
            "timestamp": get_current_timestamp(),
        }

    @staticmethod
    def _serialize(a) -> Dict[str, Any]:
        return {
            "id": a.id,
            "name": a.name,
            "user_id": a.user_id,
            "model": a.model,
            "temperature": a.temperature,
            "max_tokens": a.max_tokens,
            "greeting_message": a.greeting_message,
            "system_prompt": a.system_prompt,
            "personality": a.personality,
            "communication_style": a.communication_style,
            "voice_provider": a.voice_provider,
            "voice_id": a.voice_id,
            "voice_speed": a.voice_speed,
            "voice_pitch": a.voice_pitch,
            "is_active": a.is_active,
            "is_default": a.is_default,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "updated_at": a.updated_at.isoformat() if a.updated_at else None,
        }

    async def get_assistants(self, active_only: bool = True) -> Dict:
        try:
            assistants = self.service.get_all_assistants(active_only)
            return {
                "success": True,
                "total": len(assistants),
                "data": [self._serialize(a) for a in assistants],
            }
        except Exception as e:
            self.logger.error(f"Erro ao listar assistentes: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def create_assistant(self, assistant_data: Dict[str, Any]) -> Dict:
        try:
            user_id = assistant_data.get("user_id")
            name = assistant_data.get("name")
            if not user_id or not name:
                raise HTTPException(status_code=400, detail="user_id e name são obrigatórios")

            assistant = self.service.create_assistant(
                user_id=user_id,
                name=name,
                **{k: v for k, v in assistant_data.items() if k not in ("user_id", "name")},
            )
            return {
                "success": True,
                "message": "Assistente criada com sucesso",
                "data": self._serialize(assistant),
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Erro ao criar assistente: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_assistant_by_id(self, assistant_id: int) -> Dict:
        try:
            assistant = self.service.get_assistant_by_id(assistant_id)
            if not assistant:
                return {"success": False, "message": "Assistente não encontrada"}
            return {"success": True, "data": self._serialize(assistant)}
        except Exception as e:
            self.logger.error(f"Erro ao obter assistente: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_assistant_by_user(self, user_id: int) -> Dict:
        try:
            assistant = self.service.get_assistant_by_user(user_id)
            if not assistant:
                return {"success": False, "message": "Assistente não encontrada para este usuário"}
            return {"success": True, "data": self._serialize(assistant)}
        except Exception as e:
            self.logger.error(f"Erro ao obter assistente do usuário: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def update_assistant(self, assistant_id: int, assistant_data: Dict[str, Any]) -> Dict:
        try:
            assistant = self.service.update_assistant(assistant_id, **assistant_data)
            if not assistant:
                return {"success": False, "message": "Assistente não encontrada"}
            return {
                "success": True,
                "message": "Assistente atualizada com sucesso",
                "data": self._serialize(assistant),
            }
        except Exception as e:
            self.logger.error(f"Erro ao atualizar assistente: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def delete_assistant(self, assistant_id: int) -> Dict:
        try:
            ok = self.service.delete_assistant(assistant_id)
            if not ok:
                return {"success": False, "message": "Assistente não encontrada"}
            return {"success": True, "message": "Assistente desativada com sucesso"}
        except Exception as e:
            self.logger.error(f"Erro ao deletar assistente: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_default_assistant(self) -> Dict:
        try:
            assistant = self.service.get_default_assistant()
            if not assistant:
                return {"success": False, "message": "Assistente padrão não encontrada"}
            return {"success": True, "data": self._serialize(assistant)}
        except Exception as e:
            self.logger.error(f"Erro ao obter assistente padrão: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def set_default_assistant(self, assistant_id: int) -> Dict:
        try:
            assistant = self.service.set_default_assistant(assistant_id)
            if not assistant:
                return {"success": False, "message": "Assistente não encontrada"}
            return {
                "success": True,
                "message": "Assistente definida como padrão",
                "data": self._serialize(assistant),
            }
        except Exception as e:
            self.logger.error(f"Erro ao definir assistente padrão: {e}")
            raise HTTPException(status_code=500, detail=str(e))