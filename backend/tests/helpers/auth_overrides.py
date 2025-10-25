import types
from typing import Optional

from fastapi import FastAPI


def set_test_user(app: FastAPI, role: str = "admin") -> None:
    """Override auth dependencies to inject a deterministic test user.

    Usage in tests:
        set_test_user(app, role="admin")
    """
    try:
        from app.auth import dependencies as deps
        test_user = {
            "user_id": "test-user",
            "username": "tester",
            "role": role,
            "email": "tester@example.com",
        }
        # Best-effort override if dependency exists
        if hasattr(deps, "get_current_user"):
            app.dependency_overrides[deps.get_current_user] = lambda: test_user
        if hasattr(deps, "get_current_user_strict"):
            app.dependency_overrides[deps.get_current_user_strict] = lambda: test_user
    except Exception:
        # If auth deps not present in minimal env, ignore
        pass


def clear_auth_overrides(app: FastAPI) -> None:
    try:
        from app.auth import dependencies as deps
        if hasattr(deps, "get_current_user") and deps.get_current_user in app.dependency_overrides:
            del app.dependency_overrides[deps.get_current_user]
        if hasattr(deps, "get_current_user_strict") and deps.get_current_user_strict in app.dependency_overrides:
            del app.dependency_overrides[deps.get_current_user_strict]
    except Exception:
        pass
