# app/shared/database/__init__.py
import logging
from app.shared.database.connection import get_engine
from app.core.config.settings import Configuration

config = Configuration()


def init_db():
    """Inicializa o banco de dados e popula se configurado"""
    try:
        get_engine()

        from app.shared.database.populate import populate_database
        populate_database()

        logging.info("Banco de dados inicializado com sucesso!")
        return True
    except Exception as e:
        logging.error(f"Erro ao inicializar banco de dados: {e}")
        return False