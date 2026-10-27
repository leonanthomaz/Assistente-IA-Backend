# app/modules/assistant/services/assistant_service.py
import logging
from typing import Optional, List

from app.modules.assistant.models.assistant_model import Assistant
from app.modules.assistant.repositories.assistant_repository import AssistantRepository
from app.modules.users.repositories.user_repository import UserRepository


class AssistantService:
    """Regras de negócio de assistentes."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.repository = AssistantRepository()
        self.user_repository = UserRepository()

    # ============ LEITURA ============
    def get_all_assistants(self, active_only: bool = True) -> List[Assistant]:
        return self.repository.list(active_only=active_only)

    def get_assistant_by_id(self, assistant_id: int) -> Optional[Assistant]:
        return self.repository.get_by_id(assistant_id)

    def get_assistant_by_user(self, user_id: int) -> Optional[Assistant]:
        return self.repository.get_by_user(user_id)

    def get_default_assistant(self) -> Optional[Assistant]:
        return self.repository.get_default()

    # ============ ESCRITA ============
    def create_assistant(
        self,
        user_id: int,
        name: str,
        **kwargs,
    ) -> Assistant:
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(f"Usuário com ID {user_id} não encontrado")

        # se é o primeiro assistant do user, vira default
        existing = self.repository.get_by_user(user_id)
        if "is_default" not in kwargs:
            kwargs["is_default"] = existing is None

        return self.repository.create(
            user_id=user_id,
            name=name,
            **kwargs,
        )

    def update_assistant(self, assistant_id: int, **kwargs) -> Optional[Assistant]:
        return self.repository.update(assistant_id, **kwargs)

    def set_default_assistant(self, assistant_id: int) -> Optional[Assistant]:
        return self.repository.set_default(assistant_id)

    def delete_assistant(self, assistant_id: int) -> bool:
        """Soft delete sempre."""
        return self.repository.deactivate(assistant_id)