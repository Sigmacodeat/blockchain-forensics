"""
Chat Feedback Model - User-Feedback zu AI-Antworten
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, Text, ForeignKey
from sqlalchemy.orm import relationship
import enum
from app.db.base_class import Base


class FeedbackType(str, enum.Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"


class ChatFeedback(Base):
    """Chat-Feedback von Usern zu AI-Antworten"""
    __tablename__ = "chat_feedback"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    message_index = Column(Integer, nullable=False)
    message_content = Column(Text, nullable=False)
    feedback_type = Column(Enum(FeedbackType), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Optional: Relation zu User (wenn eingeloggt)
    # user = relationship("User", back_populates="chat_feedback")
