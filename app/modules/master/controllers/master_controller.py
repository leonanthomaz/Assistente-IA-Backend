# app/modules/master/controllers/master_controller.py
import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from app.shared.utils.retornar_timestamp import get_current_timestamp
from app.modules.master.services.master_service import MasterService


class MasterController(APIRouter):
    """Controller para operações com Master"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.service = MasterService()

        self.add_api_route(
            path="/health",
            endpoint=self.health_check,
            methods=["GET"],
            summary="Health check"
        )
        
        self.add_api_route(
            path="",
            endpoint=self.get_master_config,
            methods=["GET"],
            summary="Obtém configuração master"
        )
        
        self.add_api_route(
            path="",
            endpoint=self.update_master_config,
            methods=["PUT"],
            summary="Atualiza configuração master"
        )
    
    def health_check(self) -> Dict[str, str]:
        return {
            "status": "ONLINE",
            "service": "API MASTER",
            "timestamp": get_current_timestamp()
        }
    
    async def get_master_config(self) -> Dict:
        try:
            master = self.service.get_master_config()
            if master:
                return {"success": True, "data": master}
            return {"success": False, "message": "Configuração master não encontrada"}
        except Exception as e:
            self.logger.error(f"Erro: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def update_master_config(self, config_data: Dict[str, Any]) -> Dict:
        try:
            master = self.service.update_master_config(**config_data)
            if master:
                return {
                    "success": True,
                    "message": "Configuração atualizada com sucesso",
                    "data": master
                }
            return {"success": False, "message": "Configuração master não encontrada"}
        except Exception as e:
            self.logger.error(f"Erro: {e}")
            raise HTTPException(status_code=500, detail=str(e))