from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.email import EmailService
from app.services.ai import AIService
from app.services.notify import NotificationService
from app.models import Email, EmailAnalysis, UserPreference, get_db

logger = logging.getLogger(__name__)

class EmailScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.email_service = EmailService()
        self.ai_service = AIService()
        self.notification_service = NotificationService()
        self.db = next(get_db())
    
    def check_emails(self):
        """Background job to check for new emails."""
        logger.info("Checking for new emails...")
        
        try:
            # Get user preferences
            pref = self.db.query(UserPreference).first()
            if not pref:
                pref = UserPreference()
                self.db.add(pref)
                self.db.commit()
            
            # Get unread emails
            emails = self.email_service.get_unread_emails()
            
            for email_data in emails:
                # Check if email already exists in db
                existing = self.db.query(Email).filter(Email.email_id == email_data["id"]).first()
                if existing:
                    continue
                
                # Analyze the email
                analysis = self.ai_service.analyze_email(email_data)
                
                # Save to database
                new_email = Email(
                    email_id=email_data["id"],
                    subject=email_data["subject"],
                    sender=email_data["from"],
                    body_preview=email_data["body"][:500],
                    body_full=email_data["body"],
                    is_read=False,
                    is_archived=False
                )
                self.db.add(new_email)
                self.db.commit()
                
                # Save analysis
                new_analysis = EmailAnalysis(
                    email_id=new_email.id,
                    priority=analysis.get("priority", "medium"),
                    category=analysis.get("category", "uncategorized"),
                    summary=analysis.get("summary", ""),
                    sentiment=analysis.get("sentiment", "neutral"),
                    action_required=analysis.get("action_required", False),
                    suggested_action=analysis.get("suggested_action", "review")
                )
                self.db.add(new_analysis)
                self.db.commit()
                
                # Check for auto-archive
                if pref.auto_archive_promotions and analysis.get("category") == "promotional":
                    self.email_service.archive_email(email_data["id"])
                    new_email.is_archived = True
                    self.db.commit()
                
                # Check for auto-mark-read
                if pref.auto_mark_read and analysis.get("priority") == "low":
                    self.email_service.mark_as_read(email_data["id"])
                    new_email.is_read = True
                    self.db.commit()
                
                # Send notifications if needed
                if (pref.notification_enabled and 
                    (analysis.get("priority") == pref.priority_threshold or 
                     analysis.get("action_required", False))):
                    self.notification_service.notify_important_email(email_data, analysis)
        
        except Exception as e:
            logger.error(f"Error in email check job: {e}")
    
    def start(self):
        """Start the scheduler."""
        # Get interval from settings/DB
        try:
            pref = self.db.query(UserPreference).first()
            interval = pref.check_interval if pref else settings.CHECK_INTERVAL
        except Exception:
            interval = settings.CHECK_INTERVAL
        
        # Add job to check emails
        self.scheduler.add_job(
            self.check_emails,
            IntervalTrigger(seconds=interval),
            id='check_emails',
            replace_existing=True
        )
        
        # Start the scheduler
        self.scheduler.start()
        logger.info(f"Email scheduler started with interval: {interval} seconds")
    
    def stop(self):
        """Stop the scheduler."""
        self.scheduler.shutdown()
        logger.info("Email scheduler stopped")
    
    def update_interval(self, seconds: int):
        """Update the check interval."""
        try:
            # Update in database
            pref = self.db.query(UserPreference).first()
            if not pref:
                pref = UserPreference(check_interval=seconds)
                self.db.add(pref)
            else:
                pref.check_interval = seconds
            self.db.commit()
            
            # Update running job
            if self.scheduler.running:
                self.scheduler.reschedule_job(
                    'check_emails',
                    trigger=IntervalTrigger(seconds=seconds)
                )
            logger.info(f"Email check interval updated to {seconds} seconds")
            return True
        except Exception as e:
            logger.error(f"Failed to update check interval: {e}")
            return False

# Singleton instance
scheduler = EmailScheduler() 