"""
Comment Management Models
For entity-specific comments and discussions
"""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List


class CommentStatus(str, Enum):
    """Comment status enumeration"""
    ACTIVE = "active"
    HIDDEN = "hidden"
    DELETED = "deleted"
    PINNED = "pinned"


class Comment(BaseModel):
    """Comment model for entity discussions"""
    id: str = Field(default_factory=lambda: f"comment_{datetime.utcnow().timestamp()}")
    entity_type: str = Field(..., max_length=50)  # e.g., "case", "alert", "address", "transaction"
    entity_id: str = Field(..., max_length=100)

    # Comment content
    content: str = Field(..., max_length=5000)
    author_id: str  # User ID
    author_name: Optional[str] = None  # Cached display name

    # Status and metadata
    status: CommentStatus = CommentStatus.ACTIVE
    is_internal: bool = False  # Internal comments not visible to external users

    # Threading support
    parent_id: Optional[str] = None  # For reply threads
    thread_id: Optional[str] = None  # Thread identifier

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    edited_at: Optional[datetime] = None

    # Engagement (for future features)
    likes: List[str] = Field(default_factory=list)  # User IDs who liked
    mentions: List[str] = Field(default_factory=list)  # Mentioned user IDs

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True, arbitrary_types_allowed=True)

    def model_post_init(self, __context):
        # Ensure comment is tracked for helper functions even when instantiated directly
        comments[self.id] = self
        if not self.thread_id and self.parent_id:
            parent_comment = comments.get(self.parent_id)
            if parent_comment:
                self.thread_id = parent_comment.thread_id or parent_comment.id


class CommentThread(BaseModel):
    """Comment thread model for organizing discussions"""
    id: str = Field(default_factory=lambda: f"thread_{datetime.utcnow().timestamp()}")
    entity_type: str
    entity_id: str

    # Thread information
    title: Optional[str] = None
    is_resolved: bool = False
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None

    # Metadata
    created_by: str  # User ID who started the thread
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(use_enum_values=True, arbitrary_types_allowed=True)


class CommentQuery(BaseModel):
    """Query parameters for comments"""
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    author_id: Optional[str] = None
    status: Optional[CommentStatus] = None
    parent_id: Optional[str] = None
    thread_id: Optional[str] = None
    is_internal: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=50, le=500)
    offset: int = Field(default=0, ge=0)

    model_config = ConfigDict(use_enum_values=True, arbitrary_types_allowed=True)


# In-Memory Storage (replace with PostgreSQL in production)
comments: Dict[str, Comment] = {}
comment_threads: Dict[str, CommentThread] = {}


def create_comment(
    entity_type: str,
    entity_id: str,
    content: str,
    author_id: str,
    author_name: Optional[str] = None,
    parent_id: Optional[str] = None,
    is_internal: bool = False,
    metadata: Optional[Dict[str, Any]] = None
) -> Comment:
    """Create a new comment"""
    comment = Comment(
        entity_type=entity_type,
        entity_id=entity_id,
        content=content,
        author_id=author_id,
        author_name=author_name or author_id,
        parent_id=parent_id,
        is_internal=is_internal,
        metadata=metadata or {}
    )

    # Set thread_id for threading
    if parent_id:
        parent_comment = comments.get(parent_id)
        if parent_comment:
            comment.thread_id = parent_comment.thread_id or parent_comment.id

    comments[comment.id] = comment
    return comment


def get_comment(comment_id: str) -> Optional[Comment]:
    """Get comment by ID"""
    return comments.get(comment_id)


def update_comment(
    comment_id: str,
    content: str,
    updated_by: str
) -> Optional[Comment]:
    """Update comment content"""
    comment = comments.get(comment_id)
    if not comment:
        return None

    comment.content = content
    comment.updated_at = datetime.utcnow()
    comment.edited_at = datetime.utcnow()

    # Log edit activity (would be done in API layer)
    # log_comment_activity(comment_id, "comment_edited", f"Comment edited by {updated_by}")

    return comment


def delete_comment(comment_id: str, deleted_by: str) -> Optional[Comment]:
    """Soft delete a comment"""
    comment = comments.get(comment_id)
    if not comment:
        return None

    comment.status = CommentStatus.DELETED
    comment.updated_at = datetime.utcnow()

    # Log deletion activity
    # log_comment_activity(comment_id, "comment_deleted", f"Comment deleted by {deleted_by}")

    return comment


def like_comment(comment_id: str, user_id: str) -> Optional[Comment]:
    """Like/unlike a comment"""
    comment = comments.get(comment_id)
    if not comment:
        return None

    if user_id in comment.likes:
        comment.likes.remove(user_id)
    else:
        comment.likes.append(user_id)

    return comment


def query_comments(query: CommentQuery) -> List[Comment]:
    """Query comments with filters"""
    results = list(comments.values())

    if query.entity_type:
        results = [c for c in results if c.entity_type == query.entity_type]

    if query.entity_id:
        results = [c for c in results if c.entity_id == query.entity_id]

    if query.author_id:
        results = [c for c in results if c.author_id == query.author_id]

    if query.status:
        results = [c for c in results if c.status == query.status]

    if query.parent_id is not None:
        if query.parent_id == "":  # Root comments only
            results = [c for c in results if not c.parent_id]
        else:
            results = [c for c in results if c.parent_id == query.parent_id]

    if query.thread_id:
        results = [c for c in results if c.thread_id == query.thread_id]

    if query.is_internal is not None:
        results = [c for c in results if c.is_internal == query.is_internal]

    if query.start_date:
        results = [c for c in results if c.created_at >= query.start_date]

    if query.end_date:
        results = [c for c in results if c.created_at <= query.end_date]

    # Sort by creation date descending
    results.sort(key=lambda x: x.created_at, reverse=True)

    # Apply pagination
    return results[query.offset : query.offset + query.limit]


def get_comment_replies(comment_id: str) -> List[Comment]:
    """Get all replies to a comment"""
    return [c for c in comments.values() if c.parent_id == comment_id and c.status == CommentStatus.ACTIVE]


def get_entity_comments(entity_type: str, entity_id: str) -> List[Comment]:
    """Get all active comments for an entity"""
    return [
        c for c in comments.values()
        if c.entity_type == entity_type
        and c.entity_id == entity_id
        and c.status == CommentStatus.ACTIVE
    ]


def create_thread(
    entity_type: str,
    entity_id: str,
    title: str,
    created_by: str
) -> CommentThread:
    """Create a new comment thread"""
    thread = CommentThread(
        entity_type=entity_type,
        entity_id=entity_id,
        title=title,
        created_by=created_by
    )

    comment_threads[thread.id] = thread
    return thread


def get_thread(thread_id: str) -> Optional[CommentThread]:
    """Get thread by ID"""
    return comment_threads.get(thread_id)


def resolve_thread(thread_id: str, resolved_by: str) -> Optional[CommentThread]:
    """Mark a thread as resolved"""
    thread = comment_threads.get(thread_id)
    if not thread:
        return None

    thread.is_resolved = True
    thread.resolved_by = resolved_by
    thread.resolved_at = datetime.utcnow()

    return thread


def get_entity_threads(entity_type: str, entity_id: str) -> List[CommentThread]:
    """Get all threads for an entity"""
    return [
        t for t in comment_threads.values()
        if t.entity_type == entity_type and t.entity_id == entity_id
    ]
