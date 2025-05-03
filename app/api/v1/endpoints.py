from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging

from app.models import Email, EmailAnalysis, UserPreference, get_db
from app.services.email import EmailService
from app.services.ai import AIService
from app.scheduler import scheduler

router = APIRouter()
logger = logging.getLogger(__name__)

# Email endpoints
@router.get("/emails", response_model=List[Dict[str, Any]])
def get_emails(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    is_read: Optional[bool] = None,
    is_archived: Optional[bool] = None,
    priority: Optional[str] = None
):
    """Get emails with optional filtering."""
    query = db.query(Email)
    
    if is_read is not None:
        query = query.filter(Email.is_read == is_read)
    
    if is_archived is not None:
        query = query.filter(Email.is_archived == is_archived)
    
    if priority:
        query = query.join(EmailAnalysis).filter(EmailAnalysis.priority == priority)
    
    emails = query.offset(skip).limit(limit).all()
    
    # Convert to dict with analysis data
    result = []
    for email in emails:
        email_dict = {
            "id": email.id,
            "email_id": email.email_id,
            "subject": email.subject,
            "sender": email.sender,
            "body_preview": email.body_preview,
            "is_read": email.is_read,
            "is_archived": email.is_archived,
            "analysis": None
        }
        
        if email.analysis:
            email_dict["analysis"] = {
                "priority": email.analysis.priority,
                "category": email.analysis.category,
                "summary": email.analysis.summary,
                "action_required": email.analysis.action_required,
                "suggested_action": email.analysis.suggested_action
            }
        
        result.append(email_dict)
    
    return result

@router.get("/emails/{email_id}", response_model=Dict[str, Any])
def get_email(email_id: int, db: Session = Depends(get_db)):
    """Get a specific email by ID."""
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    result = {
        "id": email.id,
        "email_id": email.email_id,
        "subject": email.subject,
        "sender": email.sender,
        "body_full": email.body_full,
        "is_read": email.is_read,
        "is_archived": email.is_archived,
        "analysis": None
    }
    
    if email.analysis:
        result["analysis"] = {
            "priority": email.analysis.priority,
            "category": email.analysis.category,
            "summary": email.analysis.summary,
            "sentiment": email.analysis.sentiment,
            "action_required": email.analysis.action_required,
            "suggested_action": email.analysis.suggested_action
        }
    
    return result

@router.post("/emails/{email_id}/mark-read")
def mark_email_read(email_id: int, db: Session = Depends(get_db)):
    """Mark an email as read."""
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    email_service = EmailService()
    success = email_service.mark_as_read(email.email_id)
    
    if success:
        email.is_read = True
        db.commit()
        return {"success": True}
    else:
        raise HTTPException(status_code=500, detail="Failed to mark email as read")

@router.post("/emails/{email_id}/archive")
def archive_email(email_id: int, db: Session = Depends(get_db)):
    """Archive an email."""
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    email_service = EmailService()
    success = email_service.archive_email(email.email_id)
    
    if success:
        email.is_archived = True
        db.commit()
        return {"success": True}
    else:
        raise HTTPException(status_code=500, detail="Failed to archive email")

@router.post("/emails/{email_id}/suggest-reply")
def suggest_reply(email_id: int, db: Session = Depends(get_db)):
    """Get AI-suggested reply for an email."""
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    ai_service = AIService()
    email_data = {
        "subject": email.subject,
        "from": email.sender,
        "body": email.body_full
    }
    
    reply = ai_service.suggest_reply(email_data)
    return {"reply": reply}

# User preferences endpoints
@router.get("/preferences", response_model=Dict[str, Any])
def get_preferences(db: Session = Depends(get_db)):
    """Get user preferences."""
    pref = db.query(UserPreference).first()
    if not pref:
        pref = UserPreference()
        db.add(pref)
        db.commit()
    
    return {
        "check_interval": pref.check_interval,
        "notification_enabled": pref.notification_enabled,
        "auto_archive_promotions": pref.auto_archive_promotions,
        "auto_mark_read": pref.auto_mark_read,
        "priority_threshold": pref.priority_threshold
    }

@router.put("/preferences")
def update_preferences(
    preferences: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Update user preferences."""
    pref = db.query(UserPreference).first()
    if not pref:
        pref = UserPreference()
        db.add(pref)
    
    # Update fields
    if "check_interval" in preferences:
        pref.check_interval = preferences["check_interval"]
        # Update scheduler in background
        background_tasks.add_task(scheduler.update_interval, preferences["check_interval"])
    
    if "notification_enabled" in preferences:
        pref.notification_enabled = preferences["notification_enabled"]
    
    if "auto_archive_promotions" in preferences:
        pref.auto_archive_promotions = preferences["auto_archive_promotions"]
    
    if "auto_mark_read" in preferences:
        pref.auto_mark_read = preferences["auto_mark_read"]
    
    if "priority_threshold" in preferences:
        pref.priority_threshold = preferences["priority_threshold"]
    
    db.commit()
    return {"success": True}

# Manual email check
@router.post("/check-emails")
def check_emails(background_tasks: BackgroundTasks):
    """Manually trigger email check."""
    background_tasks.add_task(scheduler.check_emails)
    return {"message": "Email check started in background"}

# Test Telegram notifications
@router.post("/test-notification")
def test_notification():
    """Test Telegram notification."""
    from app.services.notify import NotificationService
    
    notification_service = NotificationService()
    success = notification_service.send_notification(
        title="Test Notification",
        message="This is a test notification from your Email Assistant."
    )
    
    return {
        "success": success,
        "message": "Notification sent successfully" if success else "Failed to send notification"
    }

# Test high priority notification
@router.post("/emails/{email_id}/test-high-priority")
def test_high_priority_notification(email_id: int, db: Session = Depends(get_db)):
    """Test high priority notification for an email."""
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    # Get or create analysis
    if not email.analysis:
        analysis = EmailAnalysis(email_id=email.id)
        db.add(analysis)
    else:
        analysis = email.analysis
    
    # Update to high priority
    analysis.priority = "high"
    db.commit()
    
    # Send notification
    from app.services.notify import NotificationService
    notification_service = NotificationService()
    
    email_data = {
        "subject": email.subject,
        "from": email.sender,
        "body": email.body_full
    }
    
    analysis_data = {
        "priority": "high",
        "summary": f"TEST: This is a high priority email from {email.sender}"
    }
    
    success = notification_service.notify_important_email(email_data, analysis_data)
    
    return {
        "success": success,
        "message": "High priority notification sent" if success else "Failed to send notification"
    } 