from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, JSON, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import datetime

from app.core.config import settings

Base = declarative_base()

class Email(Base):
    __tablename__ = "emails"
    
    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(String, unique=True, index=True)
    subject = Column(String, index=True)
    sender = Column(String, index=True)
    recipients = Column(String)
    date_received = Column(DateTime, default=datetime.datetime.utcnow)
    body_preview = Column(Text)
    body_full = Column(Text)
    mailbox = Column(String, default="INBOX")
    is_read = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    
    # Relationship to analysis
    analysis = relationship("EmailAnalysis", back_populates="email", uselist=False)

class EmailAnalysis(Base):
    __tablename__ = "email_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("emails.id"))
    priority = Column(String, default="medium")
    category = Column(String, default="uncategorized")
    summary = Column(Text)
    sentiment = Column(String, default="neutral")
    action_required = Column(Boolean, default=False)
    suggested_action = Column(String)
    
    # JSON field for additional analysis data
    additional_data = Column(JSON, default={})
    
    # Relationship to email
    email = relationship("Email", back_populates="analysis")

class UserPreference(Base):
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    check_interval = Column(Integer, default=300)  # in seconds
    notification_enabled = Column(Boolean, default=True)
    auto_archive_promotions = Column(Boolean, default=False)
    auto_mark_read = Column(Boolean, default=False)
    priority_threshold = Column(String, default="high")  # high, medium, low

# Create database engine and session
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables
def create_tables():
    Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 