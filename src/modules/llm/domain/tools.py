from dataclasses import dataclass, field
from typing import Any
import json


# ==========================================================
# Tool Definition
# ==========================================================

@dataclass(slots=True)
class ToolParameter:
    name: str
    type: str
    description: str
    required: bool = True


@dataclass(slots=True)
class Tool:
    name: str
    description: str
    parameters: list["ToolParameter"] = field(
        default_factory=list,
    )


# ==========================================================
# Tool Call
# ==========================================================

@dataclass(slots=True)
class ToolCall:
    id: str

    name: str

    arguments: dict[str, Any] | str = field(
        default_factory=dict,
    )

    def parsed_arguments(
        self,
    ) -> dict[str, Any]:

        if isinstance(
            self.arguments,
            dict,
        ):
            return self.arguments

        if isinstance(
            self.arguments,
            str,
        ):

            if not self.arguments.strip():
                return {}

            return json.loads(
                self.arguments,
            )

        return {}


# ==========================================================
# Tool Result
# ==========================================================

@dataclass(slots=True)
class ToolResult:
    tool: str

    success: bool

    result: Any = None

    error: str | None = None