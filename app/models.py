import uuid
from datetime import datetime
from datetime import timezone

from sqlalchemy import Column, String, Text, DateTime

from app.database import Base


class ChatHistory(Base):

    __tablename__ = "chat_history"

    id=Column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
    session_id=Column(String(255),nullable=False,index=True)
    role=Column(String(20),nullable=False)
    content=Column(Text,nullable=False)
    created_at=Column(
        DateTime(timezone=True),
        default=lambda:datetime.now(timezone.utc),
        nullable=False
    )

    def __repr__(self):
        return f"<ChatHistory session={self.session_id}  role={self.role}>"
