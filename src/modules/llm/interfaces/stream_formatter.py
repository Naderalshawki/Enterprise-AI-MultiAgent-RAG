import json
from typing import Any


class StreamFormatter:
    """
    Formats streaming events into a unified JSON protocol.
    """

    @staticmethod
    def start() -> str:
        return json.dumps({
            "type": "start"
        }) + "\n"

    @staticmethod
    def chunk(content: str) -> str:
        return json.dumps({
            "type": "chunk",
            "content": content,
        }) + "\n"

    @staticmethod
    def done() -> str:
        return json.dumps({
            "type": "done"
        }) + "\n"

    @staticmethod
    def error(message: str) -> str:
        return json.dumps({
            "type": "error",
            "message": message,
        }) + "\n"