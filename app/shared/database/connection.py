# app/shared/database/connection.py
import logging
from sqlmodel import create_engine, SQLModel, Session
from app.core.config.settings import Configuration

configuration = Configuration()
_engine = None


def get_engine():
    """Retorna o engine do banco de dados (singleton)"""
    global _engine

    if _engine is None:
        db_url = configuration.get_database_url()

        connect_args = {}
        if "sqlite" in db_url:
            connect_args = {"check_same_thread": False}

        _engine = create_engine(
            db_url,
            echo=False,
            connect_args=connect_args,
        )

        # Importa TODOS os modelos pra registrar no metadata
        from app.modules.master.models.master_models import Master  # noqa
        from app.modules.users.models.user_models import User  # noqa
        from app.modules.assistant.models.assistant_model import Assistant  # noqa
        from app.modules.chat.models.chat_models import Chat, ChatItem  # noqa
        from app.modules.finance.models.finance_models import Finance, FinanceItem  # noqa

        SQLModel.metadata.create_all(bind=_engine)
        logging.info(f"Banco de dados inicializado: {db_url}")

    return _engine


def get_session():
    """Retorna uma sessão do banco"""
    return Session(get_engine())