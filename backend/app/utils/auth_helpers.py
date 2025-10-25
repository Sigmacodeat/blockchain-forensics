"""
Auth Helper Functions
Hilfs-Funktionen für Authentifizierung und Multi-Tenancy
"""

from fastapi import HTTPException
from typing import Optional


def require_org_ownership(resource_org_id: Optional[str], user_org_id: Optional[str]) -> None:
    """
    Prüft ob User Zugriff auf Resource hat (gleiche Org)
    
    Args:
        resource_org_id: Org-ID der Resource
        user_org_id: Org-ID des Users
    
    Raises:
        HTTPException: 403 wenn Orgs nicht übereinstimmen oder User keine Org hat
    
    Usage:
        ```python
        @router.get("/cases/{case_id}")
        async def get_case(case_id: str, user: dict = Depends(get_current_user)):
            case = await db.fetch_one("SELECT * FROM cases WHERE id = :id", {"id": case_id})
            if not case:
                raise HTTPException(404, "Case not found")
            require_org_ownership(case['org_id'], user.get('org_id'))
            return case
        ```
    """
    # Single-user accounts (no org_id) können nur eigene Resources zugreifen
    if not resource_org_id and not user_org_id:
        return  # Both None = single-user, erlaubt
    
    if not user_org_id:
        raise HTTPException(403, "Access denied: User has no organization")
    
    if resource_org_id != user_org_id:
        raise HTTPException(403, "Access denied: Resource belongs to different organization")


def get_org_filter_clause(user_org_id: Optional[str], user_id: str) -> dict:
    """
    Generiert SQL-Filter für Org-Isolation
    
    Args:
        user_org_id: Org-ID des Users (None für single-user)
        user_id: User-ID
    
    Returns:
        {"org_id": str, "user_id": str} für WHERE-Clause
    
    Usage:
        ```python
        @router.get("/cases")
        async def list_cases(user: dict = Depends(get_current_user)):
            filters = get_org_filter_clause(user.get('org_id'), user['user_id'])
            query = '''
                SELECT * FROM cases 
                WHERE (org_id = :org_id OR created_by = :user_id)
            '''
            cases = await db.fetch_all(query, filters)
        ```
    """
    return {
        "org_id": user_org_id,
        "user_id": user_id
    }


def is_resource_accessible(
    resource_org_id: Optional[str], 
    resource_created_by: Optional[str],
    user_org_id: Optional[str], 
    user_id: str,
    user_role: str
) -> bool:
    """
    Prüft ob User Zugriff auf Resource hat
    
    Logic:
    - Admin hat immer Zugriff
    - Ressource-Creator hat Zugriff
    - Org-Mitglieder haben Zugriff auf Org-Resources
    
    Args:
        resource_org_id: Org-ID der Resource
        resource_created_by: Creator User-ID
        user_org_id: Org-ID des Users
        user_id: User-ID
        user_role: User-Rolle
    
    Returns:
        True wenn Zugriff erlaubt
    
    Usage:
        ```python
        if not is_resource_accessible(case['org_id'], case['created_by'], 
                                      user.get('org_id'), user['user_id'], user['role']):
            raise HTTPException(403, "Access denied")
        ```
    """
    # Admin hat immer Zugriff
    if user_role == "admin":
        return True
    
    # Creator hat Zugriff
    if resource_created_by == user_id:
        return True
    
    # Org-Mitglieder haben Zugriff
    if resource_org_id and resource_org_id == user_org_id:
        return True
    
    return False
