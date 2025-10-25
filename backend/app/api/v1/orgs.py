from __future__ import annotations
from typing import Any, Dict, List
import re
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Response
from pydantic import BaseModel, Field

from app.auth.dependencies import get_current_user
from app.services.org_service import org_service

router = APIRouter(prefix="/orgs", tags=["orgs"])


class OrgCreate(BaseModel):
    # Kept for documentation/schema only; request is validated manually in handler to return 400 instead of 422
    name: str = Field(..., min_length=3, max_length=64, description="Organisationsname")


class OrgOut(BaseModel):
    id: str
    name: str
    owner_id: str
    created_at: str


class OrgsOut(BaseModel):
    organizations: List[OrgOut]


class MemberOut(BaseModel):
    members: List[str]


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=OrgOut)
@router.post("", status_code=status.HTTP_201_CREATED, response_model=OrgOut)
async def create_org(payload: Dict[str, Any], current_user: dict = Depends(get_current_user)) -> OrgOut:
    # Manual validation to ensure 400 (Bad Request) instead of 422 for simple input errors
    raw_name = (payload or {}).get("name")
    if not isinstance(raw_name, str):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="name ist erforderlich")
    name = raw_name.strip()
    if len(name) < 3 or len(name) > 64:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="name Länge ungültig")
    if not re.match(r"^[A-Za-z0-9 _.-]+$", name):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="name enthält ungültige Zeichen")
    existing = await org_service.list_orgs_for_user(str(current_user["user_id"]))
    if any(o.get("name", "").strip().lower() == name.lower() for o in existing):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Organisation mit diesem Namen existiert bereits")
    meta = await org_service.create_org(
        name=name,
        owner_id=str(current_user["user_id"]),
        created_at_iso=datetime.utcnow().isoformat(),
    )
    return OrgOut(**meta)


@router.get("/", response_model=OrgsOut)
@router.get("", response_model=OrgsOut)
async def list_my_orgs(current_user: dict = Depends(get_current_user)) -> OrgsOut:
    orgs = await org_service.list_orgs_for_user(str(current_user["user_id"]))
    return OrgsOut(organizations=orgs)  # type: ignore[arg-type]


@router.get("/{org_id}", response_model=OrgOut)
async def get_org(org_id: str, current_user: dict = Depends(get_current_user)) -> OrgOut:
    meta = await org_service.get_org(org_id)
    if not meta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organisation nicht gefunden")
    # Optional: Sichtbarkeitsprüfung (Mitgliedschaft)
    orgs = await org_service.list_orgs_for_user(str(current_user["user_id"]))
    member_ids = {o["id"] for o in orgs}
    if meta["id"] not in member_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Kein Zugriff auf diese Organisation")
    return OrgOut(**meta)


@router.get("/{org_id}/members", response_model=MemberOut)
async def list_members(org_id: str, current_user: dict = Depends(get_current_user)) -> MemberOut:
    meta = await org_service.get_org(org_id)
    if not meta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organisation nicht gefunden")
    # Sichtbarkeitsprüfung
    orgs = await org_service.list_orgs_for_user(str(current_user["user_id"]))
    member_ids = {o["id"] for o in orgs}
    if meta["id"] not in member_ids:
        raise HTTPException(status_code=403, detail="Kein Zugriff auf diese Organisation")
    members = await org_service.list_members(org_id)
    return {"members": members}


@router.post("/{org_id}/members", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def add_member(org_id: str, payload: Dict[str, Any], current_user: dict = Depends(get_current_user)) -> Response:
    user_id = str(payload.get("user_id", "")).strip()
    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id erforderlich")
    ok = await org_service.add_member(org_id=org_id, requester_id=str(current_user["user_id"]), user_id=user_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Nur Owner kann Mitglieder hinzufügen oder Organisation existiert nicht")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{org_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def remove_member(org_id: str, user_id: str, current_user: dict = Depends(get_current_user)) -> Response:
    meta = await org_service.get_org(org_id)
    if not meta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organisation nicht gefunden")
    ok = await org_service.remove_member(org_id=org_id, requester_id=str(current_user["user_id"]), user_id=user_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Nur Owner kann Mitglieder entfernen oder ungültige Operation")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
