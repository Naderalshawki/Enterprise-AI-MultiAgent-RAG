import asyncio
from src.bootstrap import create_agent_service


async def main():
    svc = create_agent_service()

    print("=" * 60)
    print("TEST 1: process_question (BIContext)")
    print("=" * 60)

    ctx = await svc.process_question(
        question="كم عدد الطلاب؟",
        user_id="test_user",
    )

    print("success      :", ctx.success)
    print("answer       :", ctx.final_report)
    print("errors       :", ctx.errors)
    print("source_type  :", ctx.source_type)
    print("sources      :", ctx.selected_sources)
    print("chart_config :", ctx.chart_config)
    print("sql_query    :", ctx.sql_query)
    print("row_count    :", len(ctx.raw_data))
    print("metadata.plan:", ctx.metadata.get("plan"))


if __name__ == "__main__":
    asyncio.run(main())