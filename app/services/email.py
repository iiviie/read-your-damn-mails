import imaplib
import email
from email.header import decode_header
import datetime
from typing import List, Dict, Any, Optional
import logging

from app.core.config import settings
from app.core.security import secure_credentials, decrypt_data

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.credentials = secure_credentials()
        self.imap = None
    
    def connect(self) -> bool:
        """Connect to the IMAP server."""
        try:
            self.imap = imaplib.IMAP4_SSL(self.credentials["host"])
            password = decrypt_data(self.credentials["password"], self.credentials["key"])
            self.imap.login(self.credentials["user"], password)
            return True
        except Exception as e:
            logger.error(f"Failed to connect to email server: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from the IMAP server."""
        if self.imap:
            try:
                self.imap.logout()
            except Exception as e:
                logger.error(f"Error during logout: {e}")
    
    def get_mailboxes(self) -> List[str]:
        """Get available mailboxes/folders."""
        if not self.imap:
            if not self.connect():
                return []
        
        mailboxes = []
        try:
            status, response = self.imap.list()
            if status == 'OK':
                for mailbox in response:
                    decoded = mailbox.decode()
                    mailbox_name = decoded.split('"')[-2] if '"' in decoded else decoded.split()[-1]
                    mailboxes.append(mailbox_name)
        except Exception as e:
            logger.error(f"Error getting mailboxes: {e}")
        
        return mailboxes
    
    def get_unread_emails(self, mailbox: str = "INBOX", limit: int = 10) -> List[Dict[str, Any]]:
        """Get unread emails from specified mailbox."""
        emails = []
        
        if not self.imap:
            if not self.connect():
                return emails
        
        try:
            status, _ = self.imap.select(mailbox)
            if status != 'OK':
                logger.error(f"Failed to select mailbox {mailbox}")
                return emails
            
            status, response = self.imap.search(None, 'UNSEEN')
            if status != 'OK':
                logger.error("Failed to search for unread emails")
                return emails
            
            email_ids = response[0].split()
            # Get the latest emails first (up to limit)
            email_ids = email_ids[-limit:] if limit < len(email_ids) else email_ids
            
            for email_id in email_ids:
                status, data = self.imap.fetch(email_id, '(RFC822)')
                if status != 'OK':
                    continue
                
                raw_email = data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                # Decode email subject
                subject = decode_header(msg["Subject"])[0][0]
                if isinstance(subject, bytes):
                    subject = subject.decode()
                
                # Get sender
                from_ = msg["From"]
                
                # Get date
                date_str = msg["Date"]
                date = datetime.datetime.now()  # Default if parsing fails
                
                # Get body
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))
                        
                        if "attachment" not in content_disposition:
                            if content_type == "text/plain":
                                body = part.get_payload(decode=True).decode()
                                break
                else:
                    body = msg.get_payload(decode=True).decode()
                
                emails.append({
                    "id": email_id.decode(),
                    "subject": subject,
                    "from": from_,
                    "date": date_str,
                    "body": body[:500] + "..." if len(body) > 500 else body  # Truncate long bodies
                })
        
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
        
        return emails
    
    def mark_as_read(self, email_id: str, mailbox: str = "INBOX") -> bool:
        """Mark an email as read."""
        if not self.imap:
            if not self.connect():
                return False
        
        try:
            status, _ = self.imap.select(mailbox)
            if status != 'OK':
                return False
            
            status, _ = self.imap.store(email_id.encode(), '+FLAGS', '\\Seen')
            return status == 'OK'
        except Exception as e:
            logger.error(f"Error marking email as read: {e}")
            return False
    
    def archive_email(self, email_id: str, source_mailbox: str = "INBOX", archive_mailbox: str = "Archive") -> bool:
        """Move an email to the archive folder."""
        if not self.imap:
            if not self.connect():
                return False
        
        try:
            # Select source mailbox
            status, _ = self.imap.select(source_mailbox)
            if status != 'OK':
                return False
            
            # Copy to archive
            status, _ = self.imap.copy(email_id.encode(), archive_mailbox)
            if status != 'OK':
                return False
            
            # Delete from source
            status, _ = self.imap.store(email_id.encode(), '+FLAGS', '\\Deleted')
            if status != 'OK':
                return False
            
            # Expunge to actually remove the email
            self.imap.expunge()
            return True
        except Exception as e:
            logger.error(f"Error archiving email: {e}")
            return False 