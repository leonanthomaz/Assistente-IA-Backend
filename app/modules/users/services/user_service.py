# app/modules/users/services/user_service.py
import logging
from typing import Optional, List

from app.modules.users.repositories.user_repository import UserRepository
from app.modules.users.models.user_models import User
from app.modules.master.models.master_models import Master
from app.shared.database.connection import get_session
from app.shared.utils.password_utils import hash_password


class UserService:
    """Regras de negócio de usuários."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.repository = UserRepository()

    # ============ LEITURA ============
    def get_all_users(self, active_only: bool = True) -> List[User]:
        return self.repository.list(active_only=active_only)

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.repository.get_by_id(user_id)

    def get_user_by_username(self, username: str) -> Optional[User]:
        return self.repository.get_by_username(username)

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.repository.get_by_email(email)

    # ============ ESCRITA ============
    def create_user(
        self,
        master_id: int,
        username: str,
        email: str,
        full_name: str,
        **kwargs,
    ) -> User:
        # valida master
        session = get_session()
        try:
            master = session.get(Master, master_id)
            if not master:
                raise ValueError(f"Master com ID {master_id} não encontrado")
        finally:
            session.close()

        # valida duplicidade
        if self.repository.get_by_username(username):
            raise ValueError(f"Usuário com username '{username}' já existe")
        if self.repository.get_by_email(email):
            raise ValueError(f"Usuário com email '{email}' já existe")

        # hash de senha se vier em texto puro
        raw_password = kwargs.pop("password", None)
        password_hash = kwargs.pop("password_hash", None)
        if not password_hash and raw_password:
            password_hash = hash_password(raw_password)
        if not password_hash:
            raise ValueError("password ou password_hash é obrigatório")

        return self.repository.create(
            master_id=master_id,
            username=username,
            email=email,
            full_name=full_name,
            password_hash=password_hash,
            **kwargs,
        )

    def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        # se vier senha em texto puro, hasheia
        raw_password = kwargs.pop("password", None)
        if raw_password:
            kwargs["password_hash"] = hash_password(raw_password)
        return self.repository.update(user_id, **kwargs)

    def delete_user(self, user_id: int, soft_delete: bool = True) -> bool:
        return self.repository.delete(user_id, soft=soft_delete)