# src/modules/__init__.py

# Controllers
from app.modules.auth.controllers.auth_controller import AuthController

from app.modules.master.controllers.master_controller import MasterController
from app.modules.assistant.controllers.assistant_controller import AssistantController
from app.modules.users.controllers.user_controller import UserController
from app.modules.chat.controllers.chat_controller import ChatController
from app.modules.finance.controllers.finance_controller import FinanceController

def register_routes(app):
    # Rotas
    app.include_router(AuthController(), prefix="/api/auth", tags=["Autenticação"])
    app.include_router(MasterController(), prefix="/api/master", tags=["Rota Master"])
    app.include_router(AssistantController(), prefix="/api/assistant", tags=["Rota Assistente"])
    app.include_router(UserController(), prefix="/api/users", tags=["Rota Usuários"])
    app.include_router(ChatController(), prefix="/api/chat", tags=["Rota Chat"])
    app.include_router(FinanceController(), prefix="/api/finance", tags=["Rota Financeiro"])
 
  
