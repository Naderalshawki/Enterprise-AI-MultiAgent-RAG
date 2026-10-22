"""Trusted authorization context for the RAG boundary.

In production, the API gateway must authenticate the caller and inject these
headers after stripping any client-supplied copies. RAG never treats a body
field as the source of authorization.
"""
from dataclasses import dataclass
from typing import Optional
from fastapi import Header, HTTPException
from src.modules.rag.config.settings import rag_settings


@dataclass(frozen=True)
class TenantContext:
    tenant_id: str
    user_id: Optional[str] = None
    roles: tuple[str, ...] = ()


def get_tenant_context(
    x_tenant_id: Optional[str] = Header(default=None),
    x_user_id: Optional[str] = Header(default=None),
    x_roles: Optional[str] = Header(default=None),
) -> TenantContext:
    """Resolve tenant identity from trusted gateway context.

    Set RAG_REQUIRE_TRUSTED_CONTEXT=true in production. Local development can
    leave it false, but production deployments must not do so.
    """
    if rag_settings.require_trusted_context and not x_tenant_id:
        raise HTTPException(status_code=403, detail="سياق المؤسسة الموثوق مفقود")
    tenant_id = x_tenant_id or "__local__"
    roles = tuple(r.strip() for r in (x_roles or "").split(",") if r.strip())
    return TenantContext(tenant_id=tenant_id, user_id=x_user_id, roles=roles)


def assert_requested_tenant(requested: Optional[str], context: TenantContext) -> None:
    """Reject user-controlled tenant overrides only in institutional mode."""
    if rag_settings.require_trusted_context and requested and requested != context.tenant_id:
        raise HTTPException(status_code=403, detail="لا يسمح بتغيير نطاق المؤسسة")


def can_manage_documents(context: TenantContext) -> bool:
    return not rag_settings.require_trusted_context or bool(
        {"admin", "document_manager"}.intersection(context.roles)
    )
