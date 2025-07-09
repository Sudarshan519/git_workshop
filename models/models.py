from datetime import datetime
from sqlalchemy import Column, Integer, String,DateTime,Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
class UserSession(Base):
    __tablename__ = "user_sessions"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False)
    # image_url = Column(String, nullable=False)
    # image_label=Column(String,nullable=False)
    # section=Column(String, nullable=False)
    sessionid = Column(String, unique=True, nullable=False)
    agent_session_id=Column(String,unique=True,nullable=True)
    pdf_ready = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    user = Column(String, nullable=False)
    session_id=Column(String,nullable=False)
    message = Column(String, nullable=True)
    image = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
class AgentResponse(Base):
    __tablename__ = "agent_responses"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, nullable=False)
    output = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow  )
