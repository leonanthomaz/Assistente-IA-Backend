# test_context.py (raiz do projeto, temporário)
from app.modules.context.tools import ToolRegistry

# schemas que vão pro Groq
schemas = ToolRegistry.list_schemas()
for s in schemas:
    print(s["function"]["name"], "-", s["function"]["description"][:60])

# executa uma tool na mão
tool = ToolRegistry.get("get_finance_summary")
result = tool.handler(user_id=1)
print(result)