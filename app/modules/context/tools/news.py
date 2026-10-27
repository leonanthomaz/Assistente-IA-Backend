# app/modules/context/tools/news.py
from app.modules.context import registry
from app.modules.chat.services.google_news_service import GoogleNewsService


def _get_latest_news(user_id: int, limit: int = 5, **kwargs) -> dict:
    noticias = GoogleNewsService().buscar_noticias_recentes(limite=limit)
    return {"total": len(noticias), "news": noticias}


registry.register(
    name="get_latest_news",
    description=(
        "Retorna as notícias mais recentes do Brasil e do mundo. Use quando o usuário "
        "pedir notícias, manchetes, o que está acontecendo no mundo. NÃO use para "
        "novidades financeiras do usuário."
    ),
    parameters={
        "type": "object",
        "properties": {
            "limit": {"type": "integer", "default": 5},
        },
    },
    handler=_get_latest_news,
)