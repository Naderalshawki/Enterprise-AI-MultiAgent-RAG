from src.modules.llm.domain.entities import (
    LLMMessage,
    LLMRequest,
)
from src.modules.llm.domain.value_objects import Role


class PromptBuilder:
    """
    Builds, normalizes, and validates prompt messages
    before sending them to the selected LLM provider.
    """

    def build(
        self,
        request: LLMRequest,
    ) -> list[LLMMessage]:

        messages = self._copy_messages(request)

        messages = self._normalize(messages)

        self._validate(messages)

        return messages

    def _copy_messages(
        self,
        request: LLMRequest,
    ) -> list[LLMMessage]:

        return [
            LLMMessage(
                role=message.role,
                content=message.content,
            )
            for message in request.messages
        ]

    def _normalize(
        self,
        messages: list[LLMMessage],
    ) -> list[LLMMessage]:

        return [
            LLMMessage(
                role=message.role,
                content=message.content.strip(),
            )
            for message in messages
        ]

    def _validate(
        self,
        messages: list[LLMMessage],
    ) -> None:

        self._validate_not_empty(messages)
        self._validate_content(messages)
        self._validate_first_message(messages)
        self._validate_system_messages(messages)

    def _validate_not_empty(
        self,
        messages: list[LLMMessage],
    ) -> None:

        if not messages:
            raise ValueError(
                "Request must contain at least one message."
            )

    def _validate_content(
        self,
        messages: list[LLMMessage],
    ) -> None:

        for message in messages:

            if not message.content:
                raise ValueError(
                    "Message content cannot be empty."
                )

    def _validate_first_message(
        self,
        messages: list[LLMMessage],
    ) -> None:

        if messages[0].role == Role.ASSISTANT:
            raise ValueError(
                "The first message cannot be an assistant message."
            )

    def _validate_system_messages(
        self,
        messages: list[LLMMessage],
    ) -> None:

        system_messages = [
            message
            for message in messages
            if message.role == Role.SYSTEM
        ]

        if len(system_messages) > 1:
            raise ValueError(
                "Only one system message is allowed."
            )

        if (
            system_messages
            and messages[0].role != Role.SYSTEM
        ):
            raise ValueError(
                "System message must be the first message."
            )