from __future__ import annotations
from typing import Optional
from fastapi import Depends, HTTPException, Request, status

from app.auth.dependencies import get_current_user_strict
from app.services.org_service import org_service

async def _extract_org_id(request: Request, explicit_org_id: Optional[str]) -> str:
    # Prefer explicit param, then header X-Org-Id, then fallback raise
    if explicit_org_id:
        return explicit_org_id
    header_org = request.headers.get("X-Org-Id")
    if header_org:
        return header_org
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="org_id erforderlich (Header X-Org-Id oder Parameter)")

async def require_org_member(
    request: Request,
    org_id: Optional[str] = None,
    user: dict = Depends(get_current_user_strict),
) -> dict:
    """
    Ensures the authenticated user is a member of the given organization.
    Usage in routes:
        @router.get("/org-resource")
        async def handler(dep=Depends(require_org_member)):
            ...
    or
        async def handler(dep=Depends(lambda rq: require_org_member(rq, org_id))):
            ...
    Returns the user dict unchanged on success.
    """
    resolved = await _extract_org_id(request, org_id)
    # Verify membership via org_service
    orgs = await org_service.list_orgs_for_user(str(user["user_id"]))
    member_ids = {o["id"] for o in orgs}
    if resolved not in member_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Kein Zugriff: Nicht Mitglied der Organisation")
    return {**user, "org_id": resolved}

async def require_org_owner(
    request: Request,
    org_id: Optional[str] = None,
    user: dict = Depends(get_current_user_strict),
) -> dict:
    """Ensures the authenticated user is OWNER of the organization."""
    resolved = await _extract_org_id(request, org_id)
    meta = await org_service.get_org(resolved)
    if not meta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organisation nicht gefunden")
    if meta.get("owner_id") != str(user["user_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Nur Owner erlaubt")
    return {**user, "org_id": resolved}
