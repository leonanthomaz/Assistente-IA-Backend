# app/modules/finance/repositories/finance_repository.py
from typing import Optional, List
from datetime import datetime
from sqlmodel import select, desc

from app.shared.database.connection import get_session
from app.modules.finance.models.finance_models import Finance, FinanceItem


class FinanceRepository:
    """Comunicação com o banco para finanças."""

    # ============ FINANCE ============
    def get_by_month(self, user_id: int, reference_month: str) -> Optional[Finance]:
        session = get_session()
        try:
            return session.exec(
                select(Finance).where(
                    Finance.user_id == user_id,
                    Finance.reference_month == reference_month,
                )
            ).first()
        finally:
            session.close()

    def get_latest_open(self, user_id: int) -> Optional[Finance]:
        """Último finance aberto do usuário (o mais recente)."""
        session = get_session()
        try:
            return session.exec(
                select(Finance)
                .where(Finance.user_id == user_id, Finance.is_closed == False)  # noqa: E712
                .order_by(desc(Finance.reference_month))
                .limit(1)
            ).first()
        finally:
            session.close()

    def create(
        self,
        user_id: int,
        master_id: int,
        reference_month: str,
        reference_year: int,
    ) -> Finance:
        session = get_session()
        try:
            finance = Finance(
                master_id=master_id,
                user_id=user_id,
                reference_month=reference_month,
                reference_year=reference_year,
                is_closed=False,
            )
            session.add(finance)
            session.commit()
            session.refresh(finance)
            return finance
        finally:
            session.close()

    def update_totals(
        self,
        finance_id: int,
        total_income: float,
        total_expenses: float,
        total_balance: float,
    ) -> None:
        session = get_session()
        try:
            finance = session.get(Finance, finance_id)
            if not finance:
                return
            finance.total_income = total_income
            finance.total_expenses = total_expenses
            finance.total_balance = total_balance
            session.add(finance)
            session.commit()
        finally:
            session.close()

    def close(self, finance_id: int) -> None:
        session = get_session()
        try:
            finance = session.get(Finance, finance_id)
            if not finance:
                return
            finance.is_closed = True
            finance.closed_at = datetime.utcnow()
            session.add(finance)
            session.commit()
        finally:
            session.close()

    # ============ ITEMS ============
    def list_items(self, finance_id: int) -> List[FinanceItem]:
        session = get_session()
        try:
            return list(
                session.exec(
                    select(FinanceItem)
                    .where(FinanceItem.finance_id == finance_id)
                    .order_by(FinanceItem.transaction_date)
                ).all()
            )
        finally:
            session.close()

    def add_item(
        self,
        finance_id: int,
        description: str,
        amount: float,
        transaction_type: str,
        category: str,
        subcategory: Optional[str] = None,
        transaction_date: Optional[datetime] = None,
        due_date: Optional[datetime] = None,
        payment_date: Optional[datetime] = None,
        payment_method: Optional[str] = None,
        status: str = "pending",
        is_recurring: bool = False,
        recurring_period: Optional[str] = None,
        notes: Optional[str] = None,
        tags: Optional[str] = None,
    ) -> FinanceItem:
        session = get_session()
        try:
            item = FinanceItem(
                finance_id=finance_id,
                description=description,
                amount=amount,
                transaction_type=transaction_type,
                category=category,
                subcategory=subcategory,
                transaction_date=transaction_date or datetime.utcnow(),
                due_date=due_date,
                payment_date=payment_date,
                payment_method=payment_method,
                status=status,
                is_recurring=is_recurring,
                recurring_period=recurring_period,
                notes=notes,
                tags=tags,
            )
            session.add(item)
            session.commit()
            session.refresh(item)
            return item
        finally:
            session.close()

    def get_item(self, item_id: int) -> Optional[FinanceItem]:
        session = get_session()
        try:
            return session.get(FinanceItem, item_id)
        finally:
            session.close()

    def update_item(self, item_id: int, **kwargs) -> Optional[FinanceItem]:
        session = get_session()
        try:
            item = session.get(FinanceItem, item_id)
            if not item:
                return None
            for key, value in kwargs.items():
                if hasattr(item, key) and key not in ("id", "finance_id", "created_at"):
                    setattr(item, key, value)
            session.add(item)
            session.commit()
            session.refresh(item)
            return item
        finally:
            session.close()

    def get_item_with_owner(self, item_id: int, user_id: int) -> Optional[FinanceItem]:
        """Retorna o item só se pertencer a um finance do usuário."""
        session = get_session()
        try:
            item = session.get(FinanceItem, item_id)
            if not item:
                return None
            finance = session.get(Finance, item.finance_id)
            if not finance or finance.user_id != user_id:
                return None
            return item
        finally:
            session.close()
    
    def delete_item(self, item_id: int) -> bool:
        session = get_session()
        try:
            item = session.get(FinanceItem, item_id)
            if not item:
                return False
            session.delete(item)
            session.commit()
            return True
        finally:
            session.close()