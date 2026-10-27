from typing import Dict, Any, Callable, List

_TOOLS: Dict[str, Dict[str, Any]] = {}


def register(name: str, description: str, parameters: dict, handler: Callable) -> None:
    if name in _TOOLS:
        raise ValueError(f"Tool '{name}' já registrada")
    _TOOLS[name] = {
        "name": name,
        "description": description,
        "parameters": parameters or {"type": "object", "properties": {}},
        "handler": handler,
    }


def get(name: str):
    return _TOOLS.get(name)


def list_schemas() -> List[Dict]:
    """Formato aceito pelo Groq em `tools`."""
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["parameters"],
            },
        }
        for t in _TOOLS.values()
    ]