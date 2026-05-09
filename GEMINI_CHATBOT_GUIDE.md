# Gemini API Chatbot Implementation Guide

## Overview

Your Django hotel chatbot has been enhanced with Google's Gemini API integration. The implementation includes:

1. **`build_system_prompt(availability_data)`** - Creates comprehensive system prompts for Gemini
2. **Enhanced Keyword Chatbot** - The original keyword-based system is still available
3. **Gemini Integration** - New `GeminiChatbot` class for AI-powered conversations with graceful fallback

## Files Modified/Created

### 1. `authentication/chatbot_engine.py` (MODIFIED)
- ✅ Added `build_system_prompt(availability_data)` function
- ✅ Added `_format_availability_data(availability_data)` helper
- ✅ Original ChatbotEngine class unchanged (backward compatible)

### 2. `authentication/gemini_chatbot.py` (NEW)
- ✅ New `GeminiChatbot` class for Gemini API integration
- ✅ Utility functions for easy integration
- ✅ Fallback mechanism if API fails

### 3. `requirements.txt` (MODIFIED)
- ✅ Added `google-generativeai==0.7.0`

---

## Quick Start

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Set Up Google API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikeys)
2. Create a new API key (free tier available)
3. Add to your `.env` file:

```env
GOOGLE_API_KEY=your_api_key_here
```

### Step 3: Use in Django Views

#### Option A: Using Gemini AI (Recommended)

```python
from authentication.gemini_chatbot import chat_with_gemini_or_fallback

def chatbot_view(request):
    user_message = request.GET.get('message', '')
    
    # This uses Gemini if available, falls back to keyword system
    response_data = chat_with_gemini_or_fallback(user_message)
    
    return JsonResponse({
        'response': response_data['response'],
        'use_ai': response_data.get('use_ai', False),
        'status': response_data.get('status', 'success')
    })
```

#### Option B: Using Only Keyword-Based Chatbot (Legacy)

```python
from authentication.chatbot_engine import get_chatbot_response

def chatbot_view(request):
    user_message = request.GET.get('message', '')
    response_data = get_chatbot_response(user_message)
    
    return JsonResponse({
        'response': response_data['response'],
        'intent': response_data.get('intent'),
        'confidence': response_data.get('confidence')
    })
```

#### Option C: Direct Gemini Control

```python
from authentication.gemini_chatbot import GeminiChatbot

def chatbot_view(request):
    user_message = request.GET.get('message', '')
    
    try:
        chatbot = GeminiChatbot()
        response_data = chatbot.chat(user_message)
        
        return JsonResponse({
            'response': response_data['response'],
            'speaker': response_data.get('speaker'),
            'status': response_data.get('status')
        })
    except Exception as e:
        # Fallback to keyword system
        from authentication.chatbot_engine import get_chatbot_response
        response_data = get_chatbot_response(user_message)
        return JsonResponse({'response': response_data['response']})
```

---

## The `build_system_prompt()` Function

### Purpose
Creates a comprehensive system prompt that tells Gemini how to behave as Maya, the hotel assistant.

### Parameters

```python
availability_data: Dict[str, Any]
```

Expected keys:
- `total_rooms` (int): Total rooms in the hotel
- `available_count` (int): Currently available rooms
- `by_type` (dict): Availability by room type with 'total' and 'available' keys
- `check_date` (str): Current check date (YYYY-MM-DD)

### Returns

A formatted string containing:
- Hotel information (location, contact)
- Room types with prices and capacity
- Amenities list
- Policies (cancellation, pets, payments, house rules)
- Current availability (dynamic from availability_data)
- Maya's role and guidelines
- Rules for AI behavior

### Example Usage

```python
from authentication.chatbot_engine import build_system_prompt
from datetime import datetime

# Prepare availability data
availability_data = {
    'total_rooms': 50,
    'available_count': 42,
    'by_type': {
        'Standard': {'total': 20, 'available': 18},
        'Premium': {'total': 20, 'available': 16},
        'Suite': {'total': 10, 'available': 8}
    },
    'check_date': datetime.now().date().strftime('%Y-%m-%d')
}

# Build system prompt
prompt = build_system_prompt(availability_data)

# Use with Gemini
import google.generativeai as genai

genai.configure(api_key='your_api_key')
model = genai.GenerativeModel('gemini-pro')

full_message = f"{prompt}\n\nUser: What rooms do you have?"
response = model.generate_content(full_message)
print(response.text)
```

---

## System Prompt Contents

The prompt includes 8 main sections:

### 1. **ABOUT GRAND VISTA HOTEL**
- Location details
- Contact information
- Check-in/out times

### 2. **ROOM TYPES & PRICING**
- Pulled dynamically from database
- Capacity and amenities per type

### 3. **AMENITIES & FACILITIES**
- Hotel-wide amenities
- Dining options
- Recreation & wellness
- Transportation

### 4. **POLICIES**
- Payment methods accepted
- Cancellation policy
- Pet policy
- House rules
- Security & liability

### 5. **CURRENT ROOM AVAILABILITY**
- Dynamic availability injected from parameters
- Formatted for easy reading

### 6. **YOUR ROLE & GUIDELINES**
- Maya's personality (helpful, professional, warm)
- Core responsibilities
- Important rules

### 7. **CONVERSATION STYLE**
- How to speak to guests
- Emoji usage
- Restrictions

### 8. **DO NOT LIST**
- Clear boundaries for the AI

---

## Features

### ✅ Automatic Availability Updates
- System prompt automatically includes live database data
- Pulls current bookings and room status
- Updates on every message

### ✅ Graceful Fallback
- If Gemini API fails, automatically returns keyword-based response
- No user interruption
- Error logging for debugging

### ✅ Conversation History
- Optional tracking of multi-turn conversations
- Can be cleared between sessions

### ✅ Error Handling
- Handles blocked prompts
- Manages API rate limits
- Provides user-friendly error messages

### ✅ Backward Compatible
- Original ChatbotEngine class unchanged
- Can run both systems simultaneously
- Gradual migration possible

---

## Testing

### Test 1: Build System Prompt

```python
from authentication.chatbot_engine import build_system_prompt

# Test with minimal data
prompt = build_system_prompt({})
print("Prompt length:", len(prompt))
print("Contains 'Grand Vista Hotel':", "Grand Vista Hotel" in prompt)

# Test with full data
availability = {
    'total_rooms': 50,
    'available_count': 30,
    'by_type': {
        'Standard': {'total': 20, 'available': 15},
        'Premium': {'total': 20, 'available': 10},
        'Suite': {'total': 10, 'available': 5}
    },
    'check_date': '2024-04-16'
}
prompt = build_system_prompt(availability)
print("Includes availability:", "30 out of 50" in prompt)
```

### Test 2: Gemini Chatbot

```python
from authentication.gemini_chatbot import GeminiChatbot

try:
    chatbot = GeminiChatbot()
    
    # Test message
    response = chatbot.chat("What are your room prices?")
    print(response['response'])
    print("Status:", response['status'])
    
except Exception as e:
    print(f"Error: {e}")
    print("Make sure GOOGLE_API_KEY is set in .env")
```

### Test 3: Fallback System

```python
from authentication.gemini_chatbot import chat_with_gemini_or_fallback

# Try with AI first
response = chat_with_gemini_or_fallback("Do you have availability?")
print("Use AI:", response.get('use_ai'))
print("Response:", response['response'])

# Force keyword system
response = chat_with_gemini_or_fallback("Do you have availability?", use_ai=False)
print("Use AI:", response.get('use_ai'))
```

---

## Environment Variables

Add to your `.env` file:

```env
# Google API Configuration
GOOGLE_API_KEY=your_gemini_api_key_here

# Optional: Specify which chatbot to use by default
DEFAULT_CHATBOT=gemini  # or 'keyword'
```

---

## Integration with Django Views

### Example View with both systems

```python
from django.http import JsonResponse
from django.views import View
from authentication.gemini_chatbot import chat_with_gemini_or_fallback
from decouple import config

class ChatbotAPIView(View):
    def get(self, request):
        message = request.GET.get('message', '').strip()
        
        if not message:
            return JsonResponse({
                'error': 'Message is required',
                'response': 'Please ask me something! 😊'
            })
        
        # Try AI first if enabled, fall back to keyword system
        use_ai = config('DEFAULT_CHATBOT', 'gemini') == 'gemini'
        response_data = chat_with_gemini_or_fallback(message, use_ai=use_ai)
        
        return JsonResponse({
            'response': response_data['response'],
            'status': response_data.get('status', 'success'),
            'use_ai': response_data.get('use_ai', False),
            'speaker': response_data.get('speaker', 'Hotel Assistant'),
            'intent': response_data.get('intent'),  # From keyword system
            'original_message': message
        })
```

### In `urls.py`:

```python
from django.urls import path
from authentication.views import ChatbotAPIView

urlpatterns = [
    # ... other patterns ...
    path('api/chatbot/', ChatbotAPIView.as_view(), name='chatbot_api'),
]
```

---

## Configuration Options

### Gemini Model Selection

The current implementation uses `gemini-pro`. Other options:

```python
# In gemini_chatbot.py, change:
self.model = genai.GenerativeModel('gemini-pro')

# To:
self.model = genai.GenerativeModel('gemini-1.5-pro')  # Latest
# or
self.model = genai.GenerativeModel('gemini-1.5-flash')  # Faster, cheaper
```

### Generation Parameters

Customize in `gemini_chatbot.py`:

```python
generation_config=genai.types.GenerationConfig(
    temperature=0.7,      # 0=deterministic, 1=creative
    max_output_tokens=500,  # Response length limit
    top_p=0.9,            # Diversity parameter
)
```

---

## Troubleshooting

### "GOOGLE_API_KEY not found"
- Set `GOOGLE_API_KEY` in your `.env` file
- Restart Django server

### "google-generativeai not installed"
- Run: `pip install -r requirements.txt`
- Or: `pip install google-generativeai`

### API Rate Limiting
- Free tier: 60 requests per minute
- Consider caching responses
- Implement request throttling in views

### Blocked Responses
- Gemini API may block certain content per its safety policies
- The system returns a friendly message
- Check logs for blocked prompt details

### Fallback Not Triggering
- Check that `authentication.chatbot_engine` is properly imported
- Verify keyword-based chatbot is working in isolation
- Enable debug logging

---

## Performance Notes

1. **System Prompt Size**: ~4000-5000 tokens per request
2. **Database Queries**: Availability lookup on each message (~2-3 queries)
3. **API Latency**: ~1-3 seconds typical response time
4. **Caching**: Consider caching availability data for 5-10 minutes

---

## Next Steps

1. ✅ Install `google-generativeai`
2. ✅ Get Gemini API key from Google AI Studio
3. ✅ Add `GOOGLE_API_KEY` to `.env`
4. ✅ Update Django views to use new integration
5. ✅ Test with sample messages
6. ✅ Monitor API usage and logs
7. ✅ Adjust temperature/settings as needed

---

## Support

For issues or questions:
- Check logs: `logger.error()` outputs to Django logs
- Review Google's [Gemini API docs](https://ai.google.dev/)
- Fallback to keyword system always available
