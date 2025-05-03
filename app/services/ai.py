import google.generativeai as genai
from typing import Dict, Any, List, Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-2.0-flash-lite')
        except Exception as e:
            logger.error(f"Failed to initialize Gemini AI: {e}")
            self.model = None
    
    def analyze_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze email content using Gemini AI."""
        if not self.model:
            return {
                "priority": "unknown",
                "category": "unknown",
                "summary": "AI analysis unavailable",
                "sentiment": "neutral",
                "action_required": False
            }
        
        try:
            # Construct the prompt
            prompt = f"""
            Please analyze this email and provide the following information:
            
            Subject: {email_data.get('subject', 'No subject')}
            From: {email_data.get('from', 'Unknown sender')}
            Body: {email_data.get('body', 'No content')}
            
            Return your analysis in JSON format with these fields:
            - priority: (high, medium, low)
            - category: (work, personal, promotional, update, etc.)
            - summary: (1-2 sentence summary)
            - sentiment: (positive, negative, neutral)
            - action_required: (true/false)
            - suggested_action: (reply, archive, ignore, read later, etc.)
            
            Format your response as valid JSON only, with no additional text.
            """
            
            response = self.model.generate_content(prompt)
            
            # Extract JSON from response
            try:
                # This is a simplified version - the actual response handling would depend on Gemini's output format
                response_text = response.text
                
                # Basic error checking/defaults
                result = {
                    "priority": "medium",
                    "category": "uncategorized",
                    "summary": "Email analysis failed",
                    "sentiment": "neutral",
                    "action_required": False,
                    "suggested_action": "review"
                }
                
                # Parse Gemini output - would need to be adjusted based on actual response format
                # This is a placeholder that assumes the response is valid JSON
                import json
                try:
                    # Clean response if needed - sometimes AI models add backticks or other formatting
                    if "```json" in response_text:
                        response_text = response_text.split("```json")[1].split("```")[0].strip()
                    elif "```" in response_text:
                        response_text = response_text.split("```")[1].split("```")[0].strip()
                    
                    gemini_result = json.loads(response_text)
                    result.update(gemini_result)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse Gemini JSON response: {response_text}")
                
                return result
            
            except Exception as parsing_error:
                logger.error(f"Error parsing Gemini response: {parsing_error}")
                return {
                    "priority": "medium",
                    "category": "uncategorized",
                    "summary": f"Email from {email_data.get('from', 'unknown')} with subject '{email_data.get('subject', 'No subject')}'",
                    "sentiment": "neutral",
                    "action_required": False,
                    "suggested_action": "review"
                }
                
        except Exception as e:
            logger.error(f"Error in Gemini analysis: {e}")
            return {
                "priority": "medium",
                "category": "uncategorized",
                "summary": f"Email from {email_data.get('from', 'unknown')} with subject '{email_data.get('subject', 'No subject')}'",
                "sentiment": "neutral",
                "action_required": False,
                "suggested_action": "review"
            }
    
    def suggest_reply(self, email_data: Dict[str, Any]) -> str:
        """Generate a suggested reply to an email."""
        if not self.model:
            return "AI reply suggestions unavailable"
        
        try:
            prompt = f"""
            Please draft a concise and professional reply to this email:
            
            Subject: {email_data.get('subject', 'No subject')}
            From: {email_data.get('from', 'Unknown sender')}
            Body: {email_data.get('body', 'No content')}
            
            Keep the reply brief, professional, and appropriate to the content.
            Don't use any placeholders - write a complete response that can be sent with minimal editing.
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
        
        except Exception as e:
            logger.error(f"Error generating reply suggestion: {e}")
            return "Unable to generate reply suggestion" 