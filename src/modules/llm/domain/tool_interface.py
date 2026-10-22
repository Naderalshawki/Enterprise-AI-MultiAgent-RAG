from abc import ABC, abstractmethod

from .tools import (
    Tool,
    ToolCall,
    ToolResult,
)


class ToolInterface(ABC):
    """
    Base interface for all tools.
    """

    @property
    @abstractmethod
    def definition(
        self,
    ) -> Tool:
        """
        Returns tool definition.
        """
        ...

    @abstractmethod
    async def execute(
        self,
        call: ToolCall,
    ) -> ToolResult:
        """
        Execute tool.
        """
        ...