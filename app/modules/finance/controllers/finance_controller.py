# app/modules/finance/controllers/finance_controller.py
import logging
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, Depends, Query

from app.core.middleware.auth_dependencies import get_current_user_id
from app.core.middleware.validate_api_key import validate_internal_api_key
from app.modules.finance.schemas.finance_schemas import AddItemRequest, UpdateItemRequest
from app.modules.finance.services.finance_service import FinanceService
from app.shared.utils.retornar_timestamp import get_current_timestamp

class FinanceController(APIRouter):
    def __init__(self):
        super().__init__(dependencies=[Depends(validate_internal_api_key)])
        self.logger = logging.getLogger(__name__)
        self.service = FinanceService()

        self.add_api_route("/health", self.health_check, methods=["GET"], summary="Health check")
        self.add_api_route("/summary", self.get_summary, methods=["GET"], summary="Resumo do mês vigente ou específico")
        self.add_api_route("/summary/{reference_month}", self.get_summary_by_month, methods=["GET"], summary="Resumo de um mês específico")
        self.add_api_route("/items", self.add_item, methods=["POST"], summary="Adiciona item")
        self.add_api_route("/items/{item_id}", self.update_item, methods=["PUT"], summary="Atualiza item")
        self.add_api_route("/items/{item_id}", self.delete_item, methods=["DELETE"], summary="Remove item")

    def health_check(self) -> Dict[str, str]:
        return {"status": "ONLINE", "service": "API FINANCE", "timestamp": get_current_timestamp()}

    async def get_summary(
        self,
        reference_month: Optional[str] = Query(None, description="YYYY-MM"),
        user_id: int = Depends(get_current_user_id),
    ) -> Dict:
        try:
            return self.service.get_summary(user_id, reference_month=reference_month)
        except Exception as e:
            self.logger.error(f"Erro no summary: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_summary_by_month(
        self,
        reference_month: str,
        user_id: int = Depends(get_current_user_id),
    ) -> Dict:
        return self.service.get_summary(user_id, reference_month=reference_month)

    async def add_item(
        self,
        payload: AddItemRequest,
        user_id: int = Depends(get_current_user_id),
    ) -> Dict:
        try:
            result = self.service.add_item(
                user_id=user_id,
                description=payload.description,
                amount=payload.amount,
                transaction_type=payload.transaction_type,
                category=payload.category,
                subcategory=payload.subcategory,
                reference_month=payload.reference_month,
                status=payload.status,
                notes=payload.notes,
            )
            if not result.get("success"):
                raise HTTPException(status_code=400, detail=result.get("message"))
            return result
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Erro no add_item: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def update_item(
        self,
        item_id: int,
        payload: UpdateItemRequest,
        user_id: int = Depends(get_current_user_id),
    ) -> Dict:
        try:
            kwargs = payload.model_dump(exclude_none=True)
            result = self.service.update_item(user_id, item_id, **kwargs)
            if not result.get("success"):
                raise HTTPException(status_code=400, detail=result.get("message"))
            return result
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Erro no update_item: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def delete_item(
        self,
        item_id: int,
        user_id: int = Depends(get_current_user_id),
    ) -> Dict:
        result = self.service.delete_item(user_id, item_id)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("message"))
        return result