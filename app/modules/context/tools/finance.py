# app/modules/context/tools/finance.py
from app.modules.context import registry
from app.modules.finance.services.finance_service import FinanceService


def _get_finance_summary(user_id: int, reference_month=None, **kwargs) -> dict:
    return FinanceService().get_summary(user_id=user_id, reference_month=reference_month)


registry.register(
    name="get_finance_summary",
    description=(
        "Retorna o resumo financeiro do usuário: saldo atual, receitas, despesas, "
        "contas pagas e pendentes, categorias. Use quando o usuário perguntar "
        "sobre saldo, quanto tem na conta, gastos, contas a pagar, resumo do mês "
        "ou novidades financeiras."
    ),
    parameters={
        "type": "object",
        "properties": {
            "reference_month": {
                "type": "string",
                "description": "Mês no formato YYYY-MM. Se omitido, usa o mês vigente.",
            },
        },
    },
    handler=_get_finance_summary,
)