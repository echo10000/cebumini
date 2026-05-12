"""
Gemini API Integration for Hotel Chatbot
Provides AI-powered conversational responses using Google's Gemini API
"""

import os
import logging
from typing import Dict, Any, Optional

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("google-genai not installed. Gemini features will be unavailable.")

from decouple import config
from authentication.models import Room, Booking
from authentication.chatbot_engine import build_system_prompt


logger = logging.getLogger(__name__)


class GeminiBlockedResponse(Exception):
    """Raised when Gemini blocks a prompt or returns no usable text."""


def _generate_text(
    client: "genai.Client",
    model_name: str,
    user_message: str,
    system_prompt: str,
) -> str:
    """Generate a text response using the current Google Gen AI SDK."""
    response = client.models.generate_content(
        model=model_name,
        contents=user_message,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.7,
            max_output_tokens=500,
        ),
    )

    prompt_feedback = getattr(response, "prompt_feedback", None)
    block_reason = getattr(prompt_feedback, "block_reason", None)
    if block_reason:
        block_message = getattr(prompt_feedback, "block_reason_message", None)
        raise GeminiBlockedResponse(block_message or str(block_reason))

    if not response.text:
        raise GeminiBlockedResponse("Gemini returned an empty response.")

    return response.text


def ask_gemini(user_message: str, availability_data: Dict[str, Any]) -> str:
    """
    Send a request to Gemini API with hotel system prompt and return response.
    
    This is a simplified, direct interface to the Gemini API using modern features:
    - Uses gemini-2.5-flash model (latest, fastest)
    - Uses system_instruction parameter for proper system prompt handling
    - Fetches availability dynamically if needed
    - Returns plain text response
    
    Args:
        user_message: The user's question/message
        availability_data: Dict with room availability info:
            - 'total_rooms': int (total rooms)
            - 'available_count': int (currently available)
            - 'by_type': dict (availability by type)
            - 'check_date': str (YYYY-MM-DD)
    
    Returns:
        str: The Gemini API response text
    
    Raises:
        ValueError: If GEMINI_API_KEY is not set
        Exception: If API call fails
    
    Example:
        availability = {
            'total_rooms': 50,
            'available_count': 35,
            'by_type': {
                'Standard': {'total': 20, 'available': 18},
                'Premium': {'total': 20, 'available': 12},
                'Suite': {'total': 10, 'available': 5}
            },
            'check_date': '2024-04-16'
        }
        
        response = ask_gemini("What rooms do you have?", availability)
        print(response)
    """
    if not GEMINI_AVAILABLE:
        raise ImportError(
            "google-genai not installed. "
            "Install it with: pip install google-genai"
        )
    
    # Get API key from environment
    api_key = os.getenv('GEMINI_API_KEY') or config('GEMINI_API_KEY', default=None)
    
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY not found in environment. "
            "Please set it: export GEMINI_API_KEY=your_key_here"
        )
    
    # Build system prompt with availability data
    system_prompt = build_system_prompt(availability_data)

    client = genai.Client(api_key=api_key)
    try:
        return _generate_text(client, 'gemini-2.5-flash', user_message, system_prompt)
    finally:
        client.close()


logger = logging.getLogger(__name__)


class GeminiChatbot:
    """
    AI-powered hotel chatbot using Google's Gemini API.
    
    Features:
    - Natural language understanding and generation
    - Context-aware responses using system prompt
    - Real-time availability data integration
    - Graceful fallback to keyword-based system
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = 'gemini-2.5-flash'):
        """
        Initialize Gemini chatbot.
        
        Args:
            api_key: Google API key. If not provided, reads from GEMINI_API_KEY or GOOGLE_API_KEY env vars
            model: Gemini model to use. Defaults to 'gemini-2.5-flash' (latest, fastest)
        """
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-genai is not installed. "
                "Install it with: pip install google-genai"
            )
        
        # Try GEMINI_API_KEY first, then fall back to GOOGLE_API_KEY
        self.api_key = (
            api_key or 
            os.getenv('GEMINI_API_KEY') or 
            config('GEMINI_API_KEY', default=None) or
            config('GOOGLE_API_KEY', default=None)
        )
        
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY or GOOGLE_API_KEY not found. "
                "Please set it in your .env file or pass it directly."
            )
        
        self.model_name = model
        self.client = genai.Client(api_key=self.api_key)
        self.conversation_history = []
        self.assistant_name = "Echo"
        
    def get_current_availability(self) -> Dict[str, Any]:
        """
        Get current room availability from database.
        
        Returns:
            Dict with availability information for the system prompt
        """
        try:
            total_rooms = Room.objects.count()
            available_rooms = total_rooms  # Start with all rooms
            
            # Subtract booked rooms for today
            from datetime import datetime, timedelta
            today = datetime.now().date()
            booked_today = Booking.objects.filter(
                check_in__lte=today,
                check_out__gt=today,
                status='CONFIRMED'
            ).values_list('room_id', flat=True).distinct()
            
            available_rooms -= len(booked_today)
            
            # Get availability by room type
            availability_by_type = {}
            rooms = Room.objects.all()
            
            for room in rooms:
                room_type = room.get_room_type_display()
                if room_type not in availability_by_type:
                    availability_by_type[room_type] = {'total': 0, 'available': 0}
                
                availability_by_type[room_type]['total'] += 1
                
                if room.id not in booked_today:
                    availability_by_type[room_type]['available'] += 1
            
            return {
                'total_rooms': total_rooms,
                'available_count': available_rooms,
                'by_type': availability_by_type,
                'check_date': today.strftime('%Y-%m-%d')
            }
        except Exception as e:
            logger.error(f"Error fetching availability: {e}")
            return {
                'total_rooms': 0,
                'available_count': 0,
                'by_type': {},
                'check_date': datetime.now().date().strftime('%Y-%m-%d')
            }
    
    def build_system_context(self) -> str:
        """
        Build the system context with current availability.
        
        Returns:
            str: System prompt for Gemini
        """
        availability = self.get_current_availability()
        return build_system_prompt(availability)
    
    def chat(self, user_message: str, new_conversation: bool = False) -> Dict[str, Any]:
        """
        Send a message to Gemini and get a response.
        
        Args:
            user_message: The user's input message
            new_conversation: If True, start fresh conversation (clear history)
        
        Returns:
            Dict with 'response', 'status', and metadata
        """
        try:
            if new_conversation or not self.conversation_history:
                self.conversation_history = []
            
            # Build system prompt with current data
            system_prompt = self.build_system_context()
            
            assistant_message = _generate_text(
                self.client,
                self.model_name,
                user_message,
                system_prompt,
            )
            
            # Store in conversation history
            self.conversation_history.append({
                'role': 'user',
                'content': user_message
            })
            self.conversation_history.append({
                'role': 'assistant',
                'content': assistant_message
            })
            
            return {
                'response': assistant_message,
                'status': 'success',
                'speaker': self.assistant_name,
                'confidence': 1.0,
                'use_ai': True
            }
        
        except GeminiBlockedResponse as e:
            logger.warning(f"Blocked prompt: {e}")
            return {
                'response': "I appreciate your question, but I'm unable to respond to that right now. Please try asking something else about our hotel services. 🏨",
                'status': 'blocked',
                'speaker': self.assistant_name,
                'use_ai': True
            }
        
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return {
                'response': "I'm experiencing technical difficulties. Let me connect you with our staff. Please call +63 32 412 3456 or email info@grandvistahotel.com",
                'status': 'error',
                'speaker': self.assistant_name,
                'use_ai': True
            }
    
    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history = []
    
    def get_conversation_history(self) -> list:
        """Get full conversation history."""
        return self.conversation_history.copy()


def get_gemini_response(message: str) -> Dict[str, Any]:
    """
    Convenience function to get response from Gemini chatbot.
    
    Usage:
        response = get_gemini_response("What are your room prices?")
        print(response['response'])
    
    Args:
        message: User's question
    
    Returns:
        Dict with response and metadata
    """
    try:
        chatbot = GeminiChatbot()
        return chatbot.chat(message)
    except Exception as e:
        logger.error(f"Error initializing Gemini chatbot: {e}")
        return {
            'response': "AI services are currently unavailable. Please contact us directly at +63 32 412 3456.",
            'status': 'error',
            'use_ai': False
        }


# For Django views/API integration
def chat_with_gemini_or_fallback(message: str, use_ai: bool = True) -> Dict[str, Any]:
    """
    Chat with Gemini if available, otherwise use keyword-based chatbot.
    
    This function provides graceful fallback behavior.
    
    Args:
        message: User's message
        use_ai: Whether to attempt AI first (True) or keyword matching (False)
    
    Returns:
        Dict with response and metadata
    """
    if use_ai and GEMINI_AVAILABLE:
        try:
            return get_gemini_response(message)
        except Exception as e:
            logger.warning(f"Falling back to keyword chatbot: {e}")
    
    # Fallback to keyword-based system
    from authentication.chatbot_engine import get_chatbot_response
    response_data = get_chatbot_response(message)
    response_data['use_ai'] = False
    return response_data
