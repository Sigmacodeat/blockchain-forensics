"""
Comments API
Endpoints for entity-specific comments and discussions
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field

from app.models.comment import (
    Comment, CommentThread, CommentStatus, CommentQuery,
    create_comment, get_comment, update_comment, delete_comment, like_comment,
    query_comments, get_comment_replies, create_thread, get_thread, resolve_thread, get_entity_threads,
    comments, comment_threads
)

logger = logging.getLogger(__name__)

router = APIRouter()


# API Models
class CommentCreateRequest(BaseModel):
    """Request model for creating a comment"""
    content: str = Field(..., max_length=5000)
    parent_id: Optional[str] = None
    thread_id: Optional[str] = None
    is_internal: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CommentUpdateRequest(BaseModel):
    """Request model for updating a comment"""
    content: str = Field(..., max_length=5000)


class ThreadCreateRequest(BaseModel):
    """Request model for creating a thread"""
    title: Optional[str] = None


# Comment Endpoints
@router.post("", response_model=Comment, status_code=201)
async def create_comment_endpoint(
    entity_type: str = Query(..., max_length=50),
    entity_id: str = Query(..., max_length=100),
    request: CommentCreateRequest = Body(...),
    author_id: str = Query(...)
) -> Comment:
    """Create a new comment on an entity"""
    try:
        comment = create_comment(
            entity_type=entity_type,
            entity_id=entity_id,
            content=request.content,
            author_id=author_id,
            parent_id=request.parent_id,
            is_internal=request.is_internal,
            metadata=request.metadata
        )
        return comment
    except Exception as e:
        logger.error(f"Error creating comment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[Comment])
async def list_comments(
    entity_type: Optional[str] = Query(None, max_length=50),
    entity_id: Optional[str] = Query(None, max_length=100),
    author_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    parent_id: Optional[str] = Query(None),
    thread_id: Optional[str] = Query(None),
    is_internal: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
) -> List[Comment]:
    """List comments with optional filtering"""
    try:
        query = CommentQuery(
            entity_type=entity_type,
            entity_id=entity_id,
            author_id=author_id,
            status=CommentStatus(status) if status else None,
            parent_id=parent_id,
            thread_id=thread_id,
            is_internal=is_internal,
            limit=limit,
            offset=offset
        )

        comments_list = query_comments(query)
        return comments_list
    except Exception as e:
        logger.error(f"Error listing comments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{comment_id}", response_model=Comment)
async def get_comment_endpoint(comment_id: str) -> Comment:
    """Get a specific comment"""
    comment = get_comment(comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment


@router.put("/{comment_id}", response_model=Comment)
async def update_comment_endpoint(
    comment_id: str,
    request: CommentUpdateRequest,
    updated_by: str = Query(default="system")
) -> Comment:
    """Update a comment"""
    comment = update_comment(comment_id, request.content, updated_by)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    return comment


@router.delete("/{comment_id}")
async def delete_comment_endpoint(comment_id: str, deleted_by: str = Query(...)) -> Dict:
    """Soft delete a comment"""
    comment = delete_comment(comment_id, deleted_by)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    return {"status": "deleted", "comment_id": comment_id}


@router.post("/{comment_id}/like")
async def like_comment_endpoint(comment_id: str, user_id: str = Query(...)) -> Dict:
    """Like/unlike a comment"""
    comment = like_comment(comment_id, user_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    liked = user_id in comment.likes
    return {
        "status": "liked" if liked else "unliked",
        "comment_id": comment_id,
        "likes_count": len(comment.likes)
    }


@router.get("/{comment_id}/replies", response_model=List[Comment])
async def get_comment_replies_endpoint(comment_id: str) -> List[Comment]:
    """Get all replies to a comment"""
    replies = get_comment_replies(comment_id)
    return replies


# Thread Endpoints
@router.post("/threads", response_model=CommentThread, status_code=201)
async def create_thread_endpoint(
    entity_type: str = Query(..., max_length=50),
    entity_id: str = Query(..., max_length=100),
    request: ThreadCreateRequest = Body(...),
    created_by: str = Query(...)
) -> CommentThread:
    """Create a new comment thread"""
    try:
        thread = create_thread(
            entity_type=entity_type,
            entity_id=entity_id,
            title=request.title,
            created_by=created_by
        )
        return thread
    except Exception as e:
        logger.error(f"Error creating thread: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/threads", response_model=List[CommentThread])
async def list_threads(
    entity_type: Optional[str] = Query(None, max_length=50),
    entity_id: Optional[str] = Query(None, max_length=100)
) -> List[CommentThread]:
    """List threads for an entity"""
    try:
        threads = get_entity_threads(entity_type, entity_id)
        return threads
    except Exception as e:
        logger.error(f"Error listing threads: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/threads/{thread_id}", response_model=CommentThread)
async def get_thread_endpoint(thread_id: str) -> CommentThread:
    """Get a specific thread"""
    thread = get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return thread


@router.post("/threads/{thread_id}/resolve")
async def resolve_thread_endpoint(thread_id: str, resolved_by: str = Query(...)) -> Dict:
    """Mark a thread as resolved"""
    thread = resolve_thread(thread_id, resolved_by)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    return {"status": "resolved", "thread_id": thread_id}


# Statistics
@router.get("/stats")
async def get_comment_stats() -> Dict[str, Any]:
    """Get comment statistics"""
    total_comments = len(comments)
    active_comments = len([c for c in comments.values() if c.status == CommentStatus.ACTIVE])
    total_threads = len(comment_threads)
    resolved_threads = len([t for t in comment_threads.values() if t.is_resolved])

    # Comments by entity type
    by_entity_type = {}
    for comment in comments.values():
        entity_type = comment.entity_type
        by_entity_type[entity_type] = by_entity_type.get(entity_type, 0) + 1

    return {
        "total_comments": int(total_comments),
        "active_comments": int(active_comments),
        "total_threads": int(total_threads),
        "resolved_threads": int(resolved_threads),
        "by_entity_type": by_entity_type,
        "inactive_rate": float((total_comments - active_comments) / total_comments if total_comments > 0 else 0)
    }
