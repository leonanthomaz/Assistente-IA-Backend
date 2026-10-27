# app/modules/master/services/master_service.py
import logging
from typing import Optional, Dict, Any
from app.shared.database.connection import get_session
from app.modules.master.models.master_models import Master


class MasterService:
    """Serviço para operações com o Master"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_master_config(self) -> Optional[Dict[str, Any]]:
        """Obtém a configuração master"""
        session = get_session()
        master = session.query(Master).first()
        session.close()
        
        if not master:
            return None
        
        return {
            "id": master.id,
            "uuid": master.uuid,
            "system_name": master.system_name,
            "system_version": master.system_version,
            "is_active": master.is_active,
            "maintenance_mode": master.maintenance_mode,
            "default_language": master.default_language,
            "default_timezone": master.default_timezone,
            "description": master.description,
            "system_owner": master.system_owner,
            "created_at": master.created_at.isoformat() if master.created_at else None,
            "updated_at": master.updated_at.isoformat() if master.updated_at else None
        }
    
    def update_master_config(self, **kwargs) -> Optional[Dict[str, Any]]:
        """Atualiza a configuração master"""
        session = get_session()
        master = session.query(Master).first()
        
        if not master:
            session.close()
            return None
        
        # Atualiza os campos
        for key, value in kwargs.items():
            if hasattr(master, key):
                setattr(master, key, value)
        
        session.add(master)
        session.commit()
        session.refresh(master)
        
        # Prepara o resultado
        result = {
            "id": master.id,
            "uuid": master.uuid,
            "system_name": master.system_name,
            "system_version": master.system_version,
            "is_active": master.is_active,
            "maintenance_mode": master.maintenance_mode,
            "default_language": master.default_language,
            "default_timezone": master.default_timezone,
            "description": master.description,
            "system_owner": master.system_owner,
            "created_at": master.created_at.isoformat() if master.created_at else None,
            "updated_at": master.updated_at.isoformat() if master.updated_at else None
        }
        
        session.close()
        return result