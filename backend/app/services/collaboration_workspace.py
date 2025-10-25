from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

try:  # Optional dependency
    from app.services.case_management import case_management_service
    from app.services.case_management import Case
except Exception:  # pragma: no cover
    case_management_service = None  # type: ignore
    Case = None  # type: ignore


@dataclass
class Participant:
    user_id: str
    user_name: str
    joined_at: datetime
    cursor: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "joined_at": self.joined_at.isoformat(),
            "cursor": self.cursor or {},
        }


@dataclass
class CollaborationSession:
    case_id: str
    participants: Dict[str, Participant] = field(default_factory=dict)
    notes: List[Dict[str, Any]] = field(default_factory=list)
    chat: List[Dict[str, Any]] = field(default_factory=list)
    selections: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "participants": [p.to_dict() for p in self.participants.values()],
            "notes": self.notes[-100:],
            "chat": self.chat[-100:],
            "selections": self.selections,
        }


class CollaborationWorkspaceService:
    """In-memory collaboration sessions for investigators."""

    def __init__(self) -> None:
        self._sessions: Dict[str, CollaborationSession] = {}
        self._lock = asyncio.Lock()

    async def join_session(self, case_id: str, user_id: str, user_name: str) -> Dict[str, Any]:
        async with self._lock:
            session = self._sessions.setdefault(case_id, CollaborationSession(case_id=case_id))
            session.participants[user_id] = Participant(
                user_id=user_id,
                user_name=user_name,
                joined_at=datetime.utcnow(),
            )
            return session.snapshot()

    async def leave_session(self, case_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        async with self._lock:
            session = self._sessions.get(case_id)
            if not session:
                return None

            participant = session.participants.pop(user_id, None)
            session.selections.pop(user_id, None)

            if session.participants:
                return {
                    "case_id": case_id,
                    "user_id": user_id,
                    "user_name": participant.user_name if participant else None,
                    "participants": [p.to_dict() for p in session.participants.values()],
                }

            # Remove empty session
            self._sessions.pop(case_id, None)
            return {
                "case_id": case_id,
                "user_id": user_id,
                "user_name": participant.user_name if participant else None,
                "participants": [],
                "session_closed": True,
            }

    async def update_cursor(
        self,
        case_id: str,
        user_id: str,
        cursor: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        async with self._lock:
            session = self._sessions.get(case_id)
            if not session:
                return None
            participant = session.participants.get(user_id)
            if not participant:
                return None
            participant.cursor = cursor
            return {
                "case_id": case_id,
                "user_id": user_id,
                "cursor": cursor,
            }

    async def update_selection(
        self,
        case_id: str,
        user_id: str,
        selection: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        async with self._lock:
            session = self._sessions.get(case_id)
            if not session or user_id not in session.participants:
                return None
            session.selections[user_id] = selection
            return {
                "case_id": case_id,
                "user_id": user_id,
                "selection": selection,
            }

    async def add_note(
        self,
        case_id: str,
        user_id: str,
        user_name: str,
        text: str,
    ) -> Optional[Dict[str, Any]]:
        text = text.strip()
        if not text:
            return None

        async with self._lock:
            session = self._sessions.get(case_id)
            if not session:
                return None
            note = {
                "id": uuid.uuid4().hex,
                "case_id": case_id,
                "user_id": user_id,
                "user_name": user_name,
                "text": text,
                "created_at": datetime.utcnow().isoformat(),
            }
            session.notes.append(note)
            session.notes = session.notes[-200:]

        # Persist note to case timeline (best effort)
        if case_management_service:
            try:  # pragma: no cover - external service
                case: Optional[Case] = case_management_service.get_case(case_id)  # type: ignore[arg-type]
                if case:
                    case_management_service.add_comment(  # type: ignore[call-arg]
                        case_id=case_id,
                        user_id=user_id,
                        user_name=user_name,
                        comment=text,
                        is_internal=True,
                    )
            except Exception:
                pass

        return note

    async def add_chat_message(
        self,
        case_id: str,
        user_id: str,
        user_name: str,
        text: str,
    ) -> Optional[Dict[str, Any]]:
        text = text.strip()
        if not text:
            return None

        async with self._lock:
            session = self._sessions.get(case_id)
            if not session:
                return None
            message = {
                "id": uuid.uuid4().hex,
                "case_id": case_id,
                "user_id": user_id,
                "user_name": user_name,
                "text": text,
                "created_at": datetime.utcnow().isoformat(),
            }
            session.chat.append(message)
            session.chat = session.chat[-200:]
            return message

    async def snapshot(self, case_id: str) -> Optional[Dict[str, Any]]:
        async with self._lock:
            session = self._sessions.get(case_id)
            return session.snapshot() if session else None


collaboration_workspace = CollaborationWorkspaceService()

__all__ = ["collaboration_workspace", "CollaborationWorkspaceService"]
