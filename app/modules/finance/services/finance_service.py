# app/modules/finance/services/finance_service.py
import logging
from typing import Dict, Optional
from datetime import datetime

from app.modules.finance.repositories.finance_repository import FinanceRepository
from app.modules.users.repositories.user_repository import UserRepository
from app.shared.utils.retornar_timestamp import get_current_timestamp


class FinanceService:
    """Regras de negócio do financeiro."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.repository = FinanceRepository()
        self.user_repository = UserRepository()

    # ============ HELPERS ============
    @staticmethod
    def _month_str(dt: datetime) -> str:
        return f"{dt.year:04d}-{dt.month:02d}"

    @staticmethod
    def _prev_month(reference_month: str) -> str:
        year, month = int(reference_month[:4]), int(reference_month[5:])
        if month == 1:
            return f"{year - 1:04d}-12"
        return f"{year:04d}-{month - 1:02d}"

    def _resolve_master_id(self, user_id: int) -> Optional[int]:
        """Descobre o master_id a partir do user_id."""
        user = self.user_repository.get_by_id(user_id)
        return user.master_id if user else None

    # ============ RESOLUÇÃO / VIRADA DE MÊS ============
    def _resolve_finance(self, user_id: int, reference_month: Optional[str] = None):
        if not reference_month:
            reference_month = self._month_str(datetime.utcnow())

        finance = self.repository.get_by_month(user_id, reference_month)
        if finance:
            return finance

        master_id = self._resolve_master_id(user_id)
        if not master_id:
            return None

        prev_month_str = self._prev_month(reference_month)
        prev = self.repository.get_by_month(user_id, prev_month_str)

        opening_balance = 0.0
        if prev:
            items_prev = self.repository.list_items(prev.id)
            opening_balance = self._compute_totals(items_prev)["total_balance"]

        new_finance = self.repository.create(
            user_id=user_id,
            master_id=master_id,
            reference_month=reference_month,
            reference_year=int(reference_month[:4]),
        )

        if opening_balance:
            self.repository.add_item(
                finance_id=new_finance.id,
                description=f"Saldo herdado de {prev_month_str}",
                amount=opening_balance,
                transaction_type="income",
                category="Saldo",
                status="paid",
                transaction_date=datetime(int(reference_month[:4]), int(reference_month[5:]), 1),
            )

        return new_finance

    # ============ CÁLCULOS ============
    def _compute_totals(self, items) -> Dict:
        total_income = 0.0
        total_expenses = 0.0
        paid, pending = [], []

        for item in items:
            if item.transaction_type == "income":
                total_income += item.amount
            elif item.transaction_type == "expense":
                if item.status == "canceled":
                    continue
                total_expenses += item.amount
                (paid if item.status == "paid" else pending).append(item)

        return {
            "total_income": round(total_income, 2),
            "total_expenses": round(total_expenses, 2),
            "total_balance": round(total_income - total_expenses, 2),
            "paid_items": paid,
            "pending_items": pending,
        }

    def _compute_categories(self, items) -> Dict:
        categories: Dict[str, float] = {}
        for item in items:
            if item.transaction_type == "expense" and item.status != "canceled":
                categories[item.category] = categories.get(item.category, 0.0) + item.amount
        return {k: round(v, 2) for k, v in categories.items()}

    def _item_to_dict(self, item) -> Dict:
        return {
            "id": item.id,
            "description": item.description,
            "amount": item.amount,
            "transaction_type": item.transaction_type,
            "category": item.category,
            "subcategory": item.subcategory,
            "status": item.status,
            "transaction_date": item.transaction_date.isoformat() if item.transaction_date else None,
            "due_date": item.due_date.isoformat() if item.due_date else None,
            "payment_date": item.payment_date.isoformat() if item.payment_date else None,
            "is_recurring": item.is_recurring,
            "notes": item.notes,
        }

    # ============ CASOS DE USO ============
    def get_summary(
        self,
        user_id: int,
        reference_month: Optional[str] = None,
    ) -> Dict:
        finance = self._resolve_finance(user_id, reference_month)
        if not finance:
            return {"success": False, "message": "Usuário ou master não encontrado"}

        items = self.repository.list_items(finance.id)
        totals = self._compute_totals(items)
        categories = self._compute_categories(items)

        self.repository.update_totals(
            finance.id,
            totals["total_income"],
            totals["total_expenses"],
            totals["total_balance"],
        )

        return {
            "success": True,
            "reference_month": finance.reference_month,
            "reference_year": finance.reference_year,
            "is_closed": finance.is_closed,
            "total_income": totals["total_income"],
            "total_expenses": totals["total_expenses"],
            "total_balance": totals["total_balance"],
            "categories": categories,
            "items": {
                "income": [self._item_to_dict(i) for i in items if i.transaction_type == "income"],
                "paid": [self._item_to_dict(i) for i in totals["paid_items"]],
                "pending": [self._item_to_dict(i) for i in totals["pending_items"]],
            },
            "timestamp": get_current_timestamp(),
        }

    def add_item(
        self,
        user_id: int,
        description: str,
        amount: float,
        transaction_type: str,
        category: str,
        reference_month: Optional[str] = None,
        **kwargs,
    ) -> Dict:
        if transaction_type not in ("income", "expense"):
            return {"success": False, "message": "transaction_type inválido"}
        if amount <= 0:
            return {"success": False, "message": "amount deve ser positivo"}

        finance = self._resolve_finance(user_id, reference_month)
        if not finance:
            return {"success": False, "message": "Usuário ou master não encontrado"}

        item = self.repository.add_item(
            finance_id=finance.id,
            description=description,
            amount=amount,
            transaction_type=transaction_type,
            category=category,
            **kwargs,
        )

        self.get_summary(user_id, finance.reference_month)

        return {
            "success": True,
            "item": self._item_to_dict(item),
            "timestamp": get_current_timestamp(),
        }

    def update_item(self, user_id: int, item_id: int, **kwargs) -> Dict:
        # valida que o item pertence ao usuário
        item = self.repository.get_item_with_owner(item_id, user_id)
        if not item:
            return {"success": False, "message": "Item não encontrado"}

        # valida transaction_type se vier
        if "transaction_type" in kwargs and kwargs["transaction_type"] not in ("income", "expense"):
            return {"success": False, "message": "transaction_type inválido"}

        # valida amount se vier
        if "amount" in kwargs and kwargs["amount"] <= 0:
            return {"success": False, "message": "amount deve ser positivo"}

        updated = self.repository.update_item(item_id, **kwargs)
        if not updated:
            return {"success": False, "message": "Falha ao atualizar"}

        self.get_summary(user_id)
        return {
            "success": True,
            "item": self._item_to_dict(updated),
            "timestamp": get_current_timestamp(),
        }

    def delete_item(self, user_id: int, item_id: int) -> Dict:
        item = self.repository.get_item_with_owner(item_id, user_id)
        if not item:
            return {"success": False, "message": "Item não encontrado"}

        ok = self.repository.delete_item(item_id)
        if not ok:
            return {"success": False, "message": "Falha ao deletar"}

        return {"success": True, "timestamp": get_current_timestamp()}