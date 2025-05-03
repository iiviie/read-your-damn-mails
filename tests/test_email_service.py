import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the root directory to the path so we can import the app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.email import EmailService
from app.core.security import secure_credentials

class TestEmailService(unittest.TestCase):
    
    @patch('app.services.email.imaplib.IMAP4_SSL')
    @patch('app.services.email.secure_credentials')
    @patch('app.services.email.decrypt_data')
    def test_connection(self, mock_decrypt, mock_credentials, mock_imap):
        # Setup mocks
        mock_credentials.return_value = {
            "host": "imap.example.com",
            "user": "test@example.com",
            "password": "encrypted_password",
            "key": b"test_key"
        }
        mock_decrypt.return_value = "password123"
        mock_imap_instance = MagicMock()
        mock_imap.return_value = mock_imap_instance
        
        # Create service and test connection
        service = EmailService()
        result = service.connect()
        
        # Assertions
        self.assertTrue(result)
        mock_imap.assert_called_once_with("imap.example.com")
        mock_imap_instance.login.assert_called_once_with("test@example.com", "password123")
    
    @patch('app.services.email.imaplib.IMAP4_SSL')
    @patch('app.services.email.secure_credentials')
    @patch('app.services.email.decrypt_data')
    def test_get_mailboxes(self, mock_decrypt, mock_credentials, mock_imap):
        # Setup mocks
        mock_credentials.return_value = {
            "host": "imap.example.com",
            "user": "test@example.com",
            "password": "encrypted_password",
            "key": b"test_key"
        }
        mock_decrypt.return_value = "password123"
        mock_imap_instance = MagicMock()
        mock_imap.return_value = mock_imap_instance
        
        # Mock list response
        mock_imap_instance.list.return_value = (
            'OK', 
            [b'(\\HasNoChildren) "/" "INBOX"', 
             b'(\\HasNoChildren) "/" "Sent"',
             b'(\\HasNoChildren) "/" "Drafts"']
        )
        
        # Create service and test get_mailboxes
        service = EmailService()
        mailboxes = service.get_mailboxes()
        
        # Assertions
        self.assertEqual(len(mailboxes), 3)
        self.assertIn("INBOX", mailboxes)
        self.assertIn("Sent", mailboxes)
        self.assertIn("Drafts", mailboxes)
    
    @patch('app.services.email.imaplib.IMAP4_SSL')
    @patch('app.services.email.secure_credentials')
    @patch('app.services.email.decrypt_data')
    def test_mark_as_read(self, mock_decrypt, mock_credentials, mock_imap):
        # Setup mocks
        mock_credentials.return_value = {
            "host": "imap.example.com",
            "user": "test@example.com",
            "password": "encrypted_password",
            "key": b"test_key"
        }
        mock_decrypt.return_value = "password123"
        mock_imap_instance = MagicMock()
        mock_imap.return_value = mock_imap_instance
        
        # Mock select and store responses
        mock_imap_instance.select.return_value = ('OK', [b'1'])
        mock_imap_instance.store.return_value = ('OK', None)
        
        # Create service and test mark_as_read
        service = EmailService()
        result = service.mark_as_read("123")
        
        # Assertions
        self.assertTrue(result)
        mock_imap_instance.select.assert_called_once_with("INBOX")
        mock_imap_instance.store.assert_called_once_with(b"123", '+FLAGS', '\\Seen')

if __name__ == '__main__':
    unittest.main() 