import logging
import requests
from typing import Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.telegram_enabled = bool(settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID)
        if not self.telegram_enabled:
            logger.warning("Telegram notification not configured, falling back to console notifications")
    
    def send_notification(self, title: str, message: str, timeout: int = 10) -> bool:
        """Send a notification via Telegram."""
        if not self.telegram_enabled:
            logger.info(f"Notification (console): {title} - {message}")
            return False
        
        try:
            text = f"*{title}*\n{message}"
            url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
            params = {
                "chat_id": settings.TELEGRAM_CHAT_ID,
                "text": text,
                "parse_mode": "Markdown"
            }
            
            response = requests.post(url, params=params)
            if response.status_code == 200:
                return True
            else:
                logger.error(f"Failed to send Telegram notification: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False
    
    def notify_important_email(self, email_data: Dict[str, Any], analysis: Dict[str, Any]) -> bool:
        """Send notification for important emails."""
        if analysis.get("priority") != "high":
            return False
        
        subject = email_data.get("subject", "No subject")
        sender = email_data.get("from", "Unknown sender")
        
        title = f"Important Email: {subject[:30]}{'...' if len(subject) > 30 else ''}"
        message = f"From: {sender}\n{analysis.get('summary', '')}"
        
        return self.send_notification(title, message)
    
    def notify_action_required(self, email_data: Dict[str, Any], analysis: Dict[str, Any]) -> bool:
        """Send notification for emails requiring action."""
        if not analysis.get("action_required", False):
            return False
        
        subject = email_data.get("subject", "No subject")
        sender = email_data.get("from", "Unknown sender")
        
        title = f"Action Required: {subject[:30]}{'...' if len(subject) > 30 else ''}"
        message = f"From: {sender}\nAction: {analysis.get('suggested_action', 'Review')}"
        
        return self.send_notification(title, message) 