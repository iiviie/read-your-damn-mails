import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the root directory to the path so we can import the app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.ai import AIService

class TestAIService(unittest.TestCase):
    
    @patch('app.services.ai.genai.configure')
    @patch('app.services.ai.genai.GenerativeModel')
    def test_initialization(self, mock_model, mock_configure):
        # Setup mocks
        mock_model_instance = MagicMock()
        mock_model.return_value = mock_model_instance
        
        # Create service
        service = AIService()
        
        # Assertions
        mock_configure.assert_called_once()
        mock_model.assert_called_once_with('gemini-pro')
        self.assertEqual(service.model, mock_model_instance)
    
    @patch('app.services.ai.genai.configure')
    @patch('app.services.ai.genai.GenerativeModel')
    def test_analyze_email(self, mock_model, mock_configure):
        # Setup mocks
        mock_model_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '{"priority": "high", "category": "work", "summary": "Test summary", "sentiment": "positive", "action_required": true, "suggested_action": "reply"}'
        mock_model_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_model_instance
        
        # Test data
        email_data = {
            "subject": "Test Subject",
            "from": "test@example.com",
            "body": "This is a test email body."
        }
        
        # Create service and analyze email
        service = AIService()
        result = service.analyze_email(email_data)
        
        # Assertions
        self.assertEqual(result["priority"], "high")
        self.assertEqual(result["category"], "work")
        self.assertEqual(result["summary"], "Test summary")
        self.assertEqual(result["sentiment"], "positive")
        self.assertTrue(result["action_required"])
        self.assertEqual(result["suggested_action"], "reply")
        mock_model_instance.generate_content.assert_called_once()
    
    @patch('app.services.ai.genai.configure')
    @patch('app.services.ai.genai.GenerativeModel')
    def test_suggest_reply(self, mock_model, mock_configure):
        # Setup mocks
        mock_model_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "This is a suggested reply."
        mock_model_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_model_instance
        
        # Test data
        email_data = {
            "subject": "Test Subject",
            "from": "test@example.com",
            "body": "This is a test email body."
        }
        
        # Create service and get suggested reply
        service = AIService()
        result = service.suggest_reply(email_data)
        
        # Assertions
        self.assertEqual(result, "This is a suggested reply.")
        mock_model_instance.generate_content.assert_called_once()
    
    @patch('app.services.ai.genai.configure')
    @patch('app.services.ai.genai.GenerativeModel')
    def test_analyze_email_with_error(self, mock_model, mock_configure):
        # Setup mocks
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.side_effect = Exception("API Error")
        mock_model.return_value = mock_model_instance
        
        # Test data
        email_data = {
            "subject": "Test Subject",
            "from": "test@example.com",
            "body": "This is a test email body."
        }
        
        # Create service and analyze email
        service = AIService()
        result = service.analyze_email(email_data)
        
        # Assertions
        self.assertEqual(result["priority"], "medium")
        self.assertEqual(result["category"], "uncategorized")
        self.assertTrue("Test Subject" in result["summary"])
        self.assertEqual(result["sentiment"], "neutral")
        self.assertFalse(result["action_required"])

if __name__ == '__main__':
    unittest.main() 