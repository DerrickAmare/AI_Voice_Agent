"""
Database models for the outbound calling system
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from typing import Optional, List
import os

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), unique=True, index=True)
    name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    calls = relationship("Call", back_populates="user")
    resume_data = relationship("ResumeData", back_populates="user")
    employment_gaps = relationship("EmploymentGap", back_populates="user")

class Call(Base):
    __tablename__ = "calls"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    call_sid = Column(String(100), unique=True, index=True)
    status = Column(String(50), default="pending")  # pending, in_progress, completed, failed
    duration = Column(Integer, default=0)  # in seconds
    recording_url = Column(Text, nullable=True)
    adversarial_score = Column(Integer, default=0)  # 0-10 scale
    completion_score = Column(Float, default=0.0)  # 0.0-1.0 scale
    metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="calls")
    resume_data = relationship("ResumeData", back_populates="call")

class ResumeData(Base):
    __tablename__ = "resume_data"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    call_id = Column(Integer, ForeignKey("calls.id"))
    field_name = Column(String(100))  # e.g., "work_experience", "education", "skills"
    field_value = Column(Text)
    confidence_score = Column(Float, default=0.0)  # AI confidence in extracted data
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="resume_data")
    call = relationship("Call", back_populates="resume_data")

class EmploymentGap(Base):
    __tablename__ = "employment_gaps"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    start_date = Column(String(10))  # YYYY-MM-DD format
    end_date = Column(String(10))    # YYYY-MM-DD format
    resolved = Column(Boolean, default=False)
    suggested_industries = Column(ARRAY(String), nullable=True)
    follow_up_questions = Column(ARRAY(String), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="employment_gaps")

class CallQueue(Base):
    __tablename__ = "call_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20))
    priority = Column(Integer, default=1)  # 1=low, 5=high
    metadata = Column(JSONB, nullable=True)  # name, resume_data, etc.
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    scheduled_at = Column(DateTime, nullable=True)
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

class ConversationLog(Base):
    __tablename__ = "conversation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(Integer, ForeignKey("calls.id"))
    speaker = Column(String(10))  # "ai" or "user"
    message = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    confidence_score = Column(Float, nullable=True)
    adversarial_flags = Column(ARRAY(String), nullable=True)

# Database connection and session management
class DatabaseManager:
    def __init__(self, database_url: Optional[str] = None):
        if database_url is None:
            database_url = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/ai_voice_agent")
        
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self):
        """Create all tables"""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def close_session(self, session):
        """Close database session"""
        session.close()

# Global database manager instance
db_manager = DatabaseManager()

def get_db():
    """Dependency for FastAPI to get database session"""
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db_manager.close_session(db)
