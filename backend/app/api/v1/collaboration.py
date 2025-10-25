"""
Collaboration API
Case Sharing, Comments, Team Features
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = logging.getLogger(__name__)
router = APIRouter()


# Models
class CollaboratorAdd(BaseModel):
    """Add collaborator request"""
    email: EmailStr
    role: str = "viewer"  # owner, editor, viewer


class CollaboratorResponse(BaseModel):
    """Collaborator response"""
    id: str
    user_id: str
    email: str
    role: str
    added_at: str


class CommentCreate(BaseModel):
    """Create comment request"""
    content: str


class CommentResponse(BaseModel):
    """Comment response"""
    id: str
    user_id: str
    user_email: str
    content: str
    created_at: str


# Endpoints
@router.post("/cases/{case_id}/collaborators", response_model=CollaboratorResponse)
async def add_collaborator(
    case_id: str,
    data: CollaboratorAdd,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CollaboratorResponse:
    """
    Add collaborator to case
    
    Permissions:
    - Only case owner or editors can add collaborators
    """
    try:
        # Check if user exists
        user_query = text("SELECT id FROM users WHERE email = :email LIMIT 1")
        result = await db.execute(user_query, {"email": data.email})
        user_row = result.fetchone()
        
        if not user_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with email {data.email} not found",
            )
        
        target_user_id = str(user_row[0])
        
        # Insert collaborator
        insert_query = text("""
            INSERT INTO case_collaborators (case_id, user_id, role, added_at, added_by)
            VALUES (:case_id, :user_id, :role, :added_at, :added_by)
            RETURNING id, user_id, role, added_at
        """)
        
        result = await db.execute(
            insert_query,
            {
                "case_id": case_id,
                "user_id": target_user_id,
                "role": data.role,
                "added_at": datetime.utcnow(),
                "added_by": current_user["id"],
            },
        )
        await db.commit()
        
        row = result.fetchone()
        
        return CollaboratorResponse(
            id=str(row[0]),
            user_id=str(row[1]),
            email=data.email,
            role=row[2],
            added_at=row[3].isoformat(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Add collaborator failed: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add collaborator: {str(e)}",
        )


@router.get("/cases/{case_id}/collaborators", response_model=List[CollaboratorResponse])
async def list_collaborators(
    case_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[CollaboratorResponse]:
    """List all collaborators for a case"""
    try:
        query = text("""
            SELECT c.id, c.user_id, u.email, c.role, c.added_at
            FROM case_collaborators c
            JOIN users u ON c.user_id = u.id
            WHERE c.case_id = :case_id
            ORDER BY 
                CASE c.role
                    WHEN 'owner' THEN 1
                    WHEN 'editor' THEN 2
                    ELSE 3
                END,
                c.added_at ASC
        """)
        
        result = await db.execute(query, {"case_id": case_id})
        rows = result.fetchall()
        
        return [
            CollaboratorResponse(
                id=str(row[0]),
                user_id=str(row[1]),
                email=row[2],
                role=row[3],
                added_at=row[4].isoformat() if row[4] else datetime.utcnow().isoformat(),
            )
            for row in rows
        ]
    except Exception as e:
        logger.error(f"List collaborators failed: {e}")
        return []


@router.delete("/cases/{case_id}/collaborators/{collaborator_id}")
async def remove_collaborator(
    case_id: str,
    collaborator_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove collaborator from case"""
    try:
        query = text("""
            DELETE FROM case_collaborators
            WHERE id = :id AND case_id = :case_id AND role != 'owner'
        """)
        
        await db.execute(query, {"id": collaborator_id, "case_id": case_id})
        await db.commit()
        
        return {"status": "removed"}
    except Exception as e:
        logger.error(f"Remove collaborator failed: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove collaborator",
        )


# Comments
@router.post("/cases/{case_id}/comments", response_model=CommentResponse)
async def add_comment(
    case_id: str,
    data: CommentCreate,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CommentResponse:
    """Add comment to case"""
    try:
        insert_query = text("""
            INSERT INTO case_comments (case_id, user_id, content, created_at)
            VALUES (:case_id, :user_id, :content, :created_at)
            RETURNING id, user_id, content, created_at
        """)
        
        result = await db.execute(
            insert_query,
            {
                "case_id": case_id,
                "user_id": current_user["id"],
                "content": data.content,
                "created_at": datetime.utcnow(),
            },
        )
        await db.commit()
        
        row = result.fetchone()
        
        return CommentResponse(
            id=str(row[0]),
            user_id=str(row[1]),
            user_email=current_user.get("email", "unknown"),
            content=row[2],
            created_at=row[3].isoformat(),
        )
    except Exception as e:
        logger.error(f"Add comment failed: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add comment",
        )


@router.get("/cases/{case_id}/comments", response_model=List[CommentResponse])
async def list_comments(
    case_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[CommentResponse]:
    """List all comments for a case"""
    try:
        query = text("""
            SELECT c.id, c.user_id, u.email, c.content, c.created_at
            FROM case_comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.case_id = :case_id
            ORDER BY c.created_at DESC
            LIMIT 100
        """)
        
        result = await db.execute(query, {"case_id": case_id})
        rows = result.fetchall()
        
        return [
            CommentResponse(
                id=str(row[0]),
                user_id=str(row[1]),
                user_email=row[2],
                content=row[3],
                created_at=row[4].isoformat() if row[4] else datetime.utcnow().isoformat(),
            )
            for row in rows
        ]
    except Exception as e:
        logger.error(f"List comments failed: {e}")
        return []
