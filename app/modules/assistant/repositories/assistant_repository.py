# app/modules/assistant/repositories/assistant_repository.py
from typing import Optional, List
from sqlmodel import select

from app.shared.database.connection import get_session
from app.modules.assistant.models.assistant_model import Assistant


class AssistantRepository:
    """Comunicação com o banco para assistentes."""

    def list(self, active_only: bool = True) -> List[Assistant]:
        session = get_session()
        try:
            stmt = select(Assistant)
            if active_only:
                stmt = stmt.where(Assistant.is_active == True)  # noqa: E712
            return list(session.exec(stmt).all())
        finally:
            session.close()

    def get_by_id(self, assistant_id: int) -> Optional[Assistant]:
        session = get_session()
        try:
            return session.get(Assistant, assistant_id)
        finally:
            session.close()

    def get_by_user(self, user_id: int) -> Optional[Assistant]:
        """Retorna o assistant default e ativo do usuário."""
        session = get_session()
        try:
            return session.exec(
                select(Assistant).where(
                    Assistant.user_id == user_id,
                    Assistant.is_active == True,   # noqa: E712
                    Assistant.is_default == True,  # noqa: E712
                )
            ).first()
        finally:
            session.close()

    def get_default(self) -> Optional[Assistant]:
        """Retorna o assistant default e ativo global (primeiro que achar)."""
        session = get_session()
        try:
            return session.exec(
                select(Assistant).where(
                    Assistant.is_active == True,   # noqa: E712
                    Assistant.is_default == True,  # noqa: E712
                )
            ).first()
        finally:
            session.close()

    def create(
        self,
        user_id: int,
        name: str,
        **kwargs,
    ) -> Assistant:
        session = get_session()
        try:
            assistant = Assistant(
                user_id=user_id,
                name=name,
                **kwargs,
            )
            session.add(assistant)
            session.commit()
            session.refresh(assistant)
            return assistant
        finally:
            session.close()

    def update(self, assistant_id: int, **kwargs) -> Optional[Assistant]:
        session = get_session()
        try:
            assistant = session.get(Assistant, assistant_id)
            if not assistant:
                return None
            for key, value in kwargs.items():
                if hasattr(assistant, key) and key not in ("id", "created_at"):
                    setattr(assistant, key, value)
            session.add(assistant)
            session.commit()
            session.refresh(assistant)
            return assistant
        finally:
            session.close()

    def deactivate(self, assistant_id: int) -> bool:
        session = get_session()
        try:
            assistant = session.get(Assistant, assistant_id)
            if not assistant:
                return False
            assistant.is_active = False
            session.add(assistant)
            session.commit()
            return True
        finally:
            session.close()

    def set_default(self, assistant_id: int) -> Optional[Assistant]:
        """Marca um assistant como default e desmarca os outros do mesmo user."""
        session = get_session()
        try:
            target = session.get(Assistant, assistant_id)
            if not target:
                return None

            others = session.exec(
                select(Assistant).where(
                    Assistant.user_id == target.user_id,
                    Assistant.id != target.id,
                )
            ).all()
            for a in others:
                a.is_default = False
                session.add(a)

            target.is_default = True
            session.add(target)
            session.commit()
            session.refresh(target)
            return target
        finally:
            session.close()