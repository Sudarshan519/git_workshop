from datetime import datetime
from sqlalchemy import Column, Integer, String,DateTime,Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
class UserSession(Base):
    __tablename__ = "user_sessions"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False)
    sessionid = Column(String, unique=True, nullable=False)
    agent_session_id=Column(String,unique=True,nullable=True)
    pdf_ready = Column(Boolean, default=False)
    current_section = Column(Integer, default=1)
    current_question = Column(Integer, default=1)
    current_topic_index=Column(Integer,default=1)
    asked_questions = Column(String, nullable=True)  # JSON-encoded list of asked question IDs or texts
    topics = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

# class Topic(Base):
#     topic=Column(String,nullable=True)
#     username=Column(String,nullable=True)

    
class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    user = Column(String, nullable=False)
    session_id=Column(String,nullable=False)
    message = Column(String, nullable=True)
    image = Column(String, nullable=True)
    is_question = Column(Boolean, default=False,nullable=True)
    section=Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


class AgentResponse(Base):
    __tablename__ = "agent_responses"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, nullable=False)
    output = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow  )
