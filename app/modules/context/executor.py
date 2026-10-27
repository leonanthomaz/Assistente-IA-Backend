import json
import logging
from typing import List, Dict, Any

from app.modules.context import registry


class ToolExecutor:
    MAX_ITERATIONS = 3

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def execute(self, tool_calls: List[Dict], user_id: int) -> List[Dict]:
        messages = []

        for call in tool_calls:
            call_id = call.get("id", "")
            fn = call.get("function", {}) or {}
            name = fn.get("name", "")
            raw_args = fn.get("arguments", "{}")

            tool = registry.get(name)
            if not tool:
                messages.append(self._err(call_id, f"Tool '{name}' não encontrada"))
                continue

            try:
                args = json.loads(raw_args) if raw_args else {}
            except Exception as e:
                messages.append(self._err(call_id, f"Argumentos inválidos: {e}"))
                continue

            try:
                result = tool["handler"](user_id=user_id, **args)
                messages.append(self._ok(call_id, result))
            except Exception as e:
                self.logger.error(f"Erro na tool '{name}': {e}")
                messages.append(self._err(call_id, f"Falha: {e}"))

        return messages

    @staticmethod
    def _ok(call_id, payload):
        content = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False, default=str)
        return {"role": "tool", "tool_call_id": call_id, "content": content}

    @staticmethod
    def _err(call_id, msg):
        return {"role": "tool", "tool_call_id": call_id, "content": json.dumps({"error": msg})}