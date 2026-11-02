from __future__ import annotations

from fastapi import (
    APIRouter,
    HTTPException,
    status,
)

from pydantic import BaseModel, Field

from src.bootstrap import (
    create_agent_service,
)
from src.modules.multi_agent.domain.contracts import ToolResult


router = APIRouter(
    prefix="/bi-agent",
    tags=["AI BI Platform Agent"],
)


# ==========================================================
# Request Schema
# ==========================================================

class BIRequestSchema(BaseModel):
    """
    طلب Multi-Agent.
    """

    question: str = Field(
        ...,
        min_length=1,
        max_length=4000,
    )

    session_id: str = Field(
        default="default-session",
        description="معرف الجلسة (للمحادثات المتعددة)."
    )

    user_id: str = Field(
        default="default-user",
        description="معرف المستخدم (لحفظ الذاكرة)."
    )

    tenant_id: str = Field(
        default="default-tenant",
        description="معرف المؤسسة (لعزل بيانات الشركات)."
    )


# ==========================================================
# Endpoint
# ==========================================================

@router.post(
    "/ask",
    status_code=status.HTTP_200_OK,
    response_model=ToolResult,
)
async def ask_bi_agent(
    request: BIRequestSchema,
):

    try:

        # ------------------------------------------------------
        # Use Bootstrap Singleton
        # ------------------------------------------------------

        agent_service = (
            create_agent_service()
        )

        # ------------------------------------------------------
        # Process & Return ToolResult Directly
        # ------------------------------------------------------

        tool_result = await (
            agent_service.process_question_as_tool_result(
                question=request.question,
                user_id=request.user_id,
                session_id=request.session_id,
                tenant_id=request.tenant_id,
            )
        )

        return tool_result

    except Exception as exc:
        # ======================================================
        # إضافة طباعة الخطأ (Traceback) عشان نشوف المشكلة
        # ======================================================
        import traceback
        print("\n" + "="*50)
        print("🔥 الخطأ الحقيقي اللي بيحصل في الباك إند:")
        traceback.print_exc()
        print("="*50 + "\n")

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc