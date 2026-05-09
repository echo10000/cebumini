# Gemini Chatbot Quick Reference

## NEW: Simplified `ask_gemini()` Function

The easiest way to use Gemini API with your hotel chatbot:

```python
from authentication.gemini_chatbot import ask_gemini

# Get availability data
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

# Get response - just one line!
response = ask_gemini("What are your room prices?", availability)
print(response)  # Maya's response as plain string
```

**That's it!** No classes, no configuration, just simple function call.

### Features
- ✅ Uses modern Gemini 2.5 Flash model (latest, fastest)
- ✅ Uses `system_instruction` parameter (proper system prompt handling)
- ✅ Returns plain text (not dict)
- ✅ Reads `GEMINI_API_KEY` from environment
- ✅ Automatically builds system prompt with availability data

---

```bash
# 1. Update dependencies
pip install -r requirements.txt

# 2. Set Google API Key in .env
echo "GOOGLE_API_KEY=your_key_from_aistudio_google_com" >> .env
```

## Core Function: `build_system_prompt()`

Creates a system prompt for Gemini that tells it how to behave as Maya, your hotel assistant.

### Function Signature

```python
def build_system_prompt(availability_data: Dict[str, Any]) -> str:
    """
    Returns a formatted string system prompt for Gemini.
    
    Args:
        availability_data: Dict with:
            - 'total_rooms': int
            - 'available_count': int  
            - 'by_type': dict mapping room types to {'total': int, 'available': int}
            - 'check_date': str (YYYY-MM-DD format)
    
    Returns:
        Full system prompt string (~4000-5000 chars)
    """
```

### Basic Usage Example

```python
from authentication.chatbot_engine import build_system_prompt

# Prepare availability data
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

# Get system prompt
prompt = build_system_prompt(availability)
print(prompt)  # ~4000 chars of hotel info + policies + Maya's instructions
```

## Using with Gemini API

### Minimal Setup

```python
import google.generativeai as genai
from authentication.chatbot_engine import build_system_prompt

# Configure API
genai.configure(api_key='your_api_key')

# Build prompt
availability = {...}  # Your availability data
system_prompt = build_system_prompt(availability)

# Chat
model = genai.GenerativeModel('gemini-pro')
response = model.generate_content(
    f"{system_prompt}\n\nUser: What are your room prices?",
    generation_config=genai.types.GenerationConfig(temperature=0.7)
)
print(response.text)
```

### Using GeminiChatbot Class

```python
from authentication.gemini_chatbot import GeminiChatbot

# Initialize
chatbot = GeminiChatbot()  # Reads GOOGLE_API_KEY from env

# Chat
response = chatbot.chat("Do you have availability?")
print(response['response'])     # The AI's response
print(response['status'])       # 'success', 'error', 'blocked'
print(response['use_ai'])       # True if AI was used

# Start new conversation
response = chatbot.chat("Tell me your policies", new_conversation=True)

# Clear history
chatbot.clear_history()
```

### With Fallback to Keyword System

```python
from authentication.gemini_chatbot import chat_with_gemini_or_fallback

# Tries Gemini first, falls back to keyword system
response = chat_with_gemini_or_fallback("What are your amenities?")
print(response['response'])
print(response.get('use_ai'))  # True=Gemini, False=Keyword system
```

## In Django Views

### API View with Gemini & Fallback

```python
from django.http import JsonResponse
from django.views import View
from authentication.gemini_chatbot import chat_with_gemini_or_fallback

class ChatbotView(View):
    def get(self, request):
        message = request.GET.get('message', '').strip()
        
        response = chat_with_gemini_or_fallback(message)
        
        return JsonResponse({
            'response': response['response'],
            'use_ai': response.get('use_ai', False),
            'status': response.get('status', 'success')
        })
```

### URL Configuration

```python
# urls.py
from django.urls import path
from authentication.views import ChatbotView

urlpatterns = [
    path('api/chat/', ChatbotView.as_view()),
]
```

## System Prompt Contents

The prompt tells Gemini to be:

1. **Named Maya** - A hotel assistant for Grand Vista Hotel
2. **Knowledgeable** - About rooms, prices, policies, amenities
3. **Helpful** - Recommending rooms, answering questions
4. **Honest** - "Let me connect you with staff" if unsure
5. **Bounded** - Only answer hotel questions, never make up info

### What's Included

- Hotel location & contact info
- Room types, prices & capacities (from database)
- Amenities (24/7 front desk, WiFi, parking, etc.)
- Policies (cancellation, pets, payments, house rules)
- **DYNAMIC** current availability (from availability_data parameter)
- Guidelines & restrictions for responsible AI

## Common Patterns

### Pattern 1: Direct Database Integration

```python
from datetime import datetime, timedelta
from authentication.models import Room, Booking
from authentication.chatbot_engine import build_system_prompt

def get_availability():
    """Get current availability for prompt."""
    today = datetime.now().date()
    
    total = Room.objects.count()
    booked = Booking.objects.filter(
        check_in__lte=today,
        check_out__gt=today,
        status='CONFIRMED'
    ).values_list('room_id', flat=True).distinct()
    
    availability_by_type = {}
    for room in Room.objects.all():
        room_type = room.get_room_type_display()
        if room_type not in availability_by_type:
            availability_by_type[room_type] = {'total': 0, 'available': 0}
        
        availability_by_type[room_type]['total'] += 1
        if room.id not in booked:
            availability_by_type[room_type]['available'] += 1
    
    return {
        'total_rooms': total,
        'available_count': total - len(booked),
        'by_type': availability_by_type,
        'check_date': today.strftime('%Y-%m-%d')
    }

# Use it
availability = get_availability()
prompt = build_system_prompt(availability)
```

### Pattern 2: Error Handling with Fallback

```python
from authentication.gemini_chatbot import chat_with_gemini_or_fallback
from authentication.chatbot_engine import get_chatbot_response
import logging

logger = logging.getLogger(__name__)

def safe_chat(message, prefer_ai=True):
    """Chat with error handling."""
    try:
        response = chat_with_gemini_or_fallback(message, use_ai=prefer_ai)
        return response
    except Exception as e:
        logger.exception(f"Chat error: {e}")
        # Emergency fallback
        return get_chatbot_response(message)
```

### Pattern 3: Multi-turn Conversations

```python
from authentication.gemini_chatbot import GeminiChatbot

def start_conversation():
    """Start a new conversation session."""
    chatbot = GeminiChatbot()
    return chatbot

def continue_conversation(chatbot, user_message):
    """Continue existing conversation."""
    response = chatbot.chat(user_message, new_conversation=False)
    return response

def end_conversation(chatbot):
    """End conversation and get history."""
    history = chatbot.get_conversation_history()
    chatbot.clear_history()
    return history

# Usage
chatbot = start_conversation()
r1 = continue_conversation(chatbot, "Do you have rooms?")
r2 = continue_conversation(chatbot, "What about a suite?")
history = end_conversation(chatbot)
```

## Response Format

All chatbot functions return a dictionary:

```python
{
    'response': str,              # The main response text
    'status': str,                # 'success', 'error', 'blocked'
    'use_ai': bool,               # True=Gemini, False=keyword
    'speaker': str,               # Usually "Maya"
    'intent': str,                # From keyword system (if applicable)
    'confidence': float,          # Intent confidence (0-1)
}
```

## Testing

```bash
# Run complete test suite
python manage.py shell < test_gemini_chatbot.py

# Or interactive Django shell
python manage.py shell

# Build prompt
from authentication.chatbot_engine import build_system_prompt
prompt = build_system_prompt({'total_rooms': 50, 'available_count': 35})
print(len(prompt))

# Test Gemini
from authentication.gemini_chatbot import GeminiChatbot
chatbot = GeminiChatbot()
resp = chatbot.chat("What are your amenities?")
print(resp['response'])

# Test keyword system
from authentication.chatbot_engine import get_chatbot_response
resp = get_chatbot_response("How do I book?")
print(resp['response'])
```

## Environment Setup

### .env File Template

```env
# Google Gemini API
GOOGLE_API_KEY=your_key_from_https_colon_slash_slash_aistudio.google.com_slash_app_slash_apikeys

# Chatbot preferences
DEFAULT_CHATBOT=gemini  # or 'keyword'
CHATBOT_TEMPERATURE=0.7  # 0=deterministic, 1=creative
CHATBOT_MAX_TOKENS=500
```

### Debug Logging

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'chatbot.log',
        },
    },
    'loggers': {
        'authentication.gemini_chatbot': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

## Performance Tips

1. **Cache Availability** - Refresh every 5-10 minutes instead of per request
2. **Rate Limiting** - Free tier: 60 requests/minute
3. **Response Caching** - Store common questions/answers
4. **Async Processing** - Use Celery for long-running requests
5. **Model Choice** - Use `gemini-1.5-flash` for faster/cheaper responses

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "API key not found" | Set `GOOGLE_API_KEY` in `.env` |
| Import error: google.generativeai | Run `pip install google-generativeai` |
| Slow responses | Use `gemini-1.5-flash` instead of `gemini-pro` |
| Rate limited | Implement caching and request throttling |
| Blocked responses | Check logs; adjust system prompt if needed |
| Fallback not working | Verify keyword system works in isolation |

## Links

- **Get API Key**: https://aistudio.google.com/app/apikeys
- **Gemini Docs**: https://ai.google.dev/
- **Free Tier**: 60 requests/minute, great for small/medium hotels
- **Full Guide**: See `GEMINI_CHATBOT_GUIDE.md`
