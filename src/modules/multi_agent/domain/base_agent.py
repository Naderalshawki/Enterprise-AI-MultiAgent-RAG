from __future__ import annotations
from abc import ABC, abstractmethod
import logging
from src.modules.llm.application.services import LLMService
from src.modules.multi_agent.domain.bi_context import BIContext
logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """
    The abstract base class for all agents.
    """
    def __init__(self, llm_service: LLMService):
        self._llm = llm_service

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    async def execute(self, context: BIContext) -> BIContext:
        pass

    def _log_start(self):
        logger.info(f"🚀 [{self.name}] Agent started processing.")

    def _log_completion(self):
        logger.info(f"✅ [{self.name}] Agent completed processing successfully.")