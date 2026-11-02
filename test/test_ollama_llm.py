import asyncio

from src.bootstrap import create_llm_service
from src.modules.llm.domain.entities import LLMRequest, LLMMessage
from src.modules.llm.domain.value_objects import ProviderName, Role

async def test():
    print("=" * 60)
    print("TESTING OLLAMA THROUGH LLM SERVICE")
    print("=" * 60)

    service = create_llm_service()

    request = LLMRequest(
        provider=ProviderName.OLLAMA,
        model="qwen2.5:1.5b",  # <--- تم التعديل إلى النموذج المحلي الذي قمت بتنزيله
        messages=[
            LLMMessage(
                role=Role.USER,
                content="Write a Python Hello World program."
            )
        ],
        temperature=0.2,
        max_tokens=100,
    )

    print("\nSending request to Ollama...\n")

    response = await service.generate(request)

    print("PROVIDER:", response.provider)
    print("MODEL:", response.model)

    print("\nRESPONSE:")
    print("-" * 60)
    print(response.content)
    print("-" * 60)

    print("\nTOKEN USAGE:")
    print("Prompt:", response.usage.prompt_tokens)
    print("Completion:", response.usage.completion_tokens)
    print("Total:", response.usage.total_tokens)

if __name__ == "__main__":
    asyncio.run(test())