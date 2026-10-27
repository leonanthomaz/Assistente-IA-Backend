# app/modules/users/repositories/user_repository.py
from typing import Optional, List
from sqlmodel import select

from app.shared.database.connection import get_session
from app.modules.users.models.user_models import User


class UserRepository:
    """Comunicação com o banco para usuários."""

    def list(self, active_only: bool = True) -> List[User]:
        session = get_session()
        try:
            stmt = select(User)
            if active_only:
                stmt = stmt.where(User.is_active == True)  # noqa: E712
            return list(session.exec(stmt).all())
        finally:
            session.close()

    def get_by_id(self, user_id: int) -> Optional[User]:
        session = get_session()
        try:
            return session.get(User, user_id)
        finally:
            session.close()

    def get_by_username(self, username: str) -> Optional[User]:
        session = get_session()
        try:
            return session.exec(
                select(User).where(User.username == username)
            ).first()
        finally:
            session.close()

    def get_by_email(self, email: str) -> Optional[User]:
        session = get_session()
        try:
            return session.exec(
                select(User).where(User.email == email)
            ).first()
        finally:
            session.close()

    def create(
        self,
        master_id: int,
        username: str,
        email: str,
        full_name: str,
        password_hash: str,
        **kwargs,
    ) -> User:
        session = get_session()
        try:
            user = User(
                master_id=master_id,
                username=username,
                email=email,
                full_name=full_name,
                password_hash=password_hash,
                **kwargs,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            return user
        finally:
            session.close()

    def update(self, user_id: int, **kwargs) -> Optional[User]:
        session = get_session()
        try:
            user = session.get(User, user_id)
            if not user:
                return None
            for key, value in kwargs.items():
                if hasattr(user, key) and key not in ("id", "created_at"):
                    setattr(user, key, value)
            session.add(user)
            session.commit()
            session.refresh(user)
            return user
        finally:
            session.close()

    def delete(self, user_id: int, soft: bool = True) -> bool:
        session = get_session()
        try:
            user = session.get(User, user_id)
            if not user:
                return False
            if soft:
                user.is_active = False
                session.add(user)
            else:
                session.delete(user)
            session.commit()
            return True
        finally:
            session.close()