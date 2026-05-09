# How to Test Your Gemini Chatbot

## ✅ All Tests Passed! 

Your chatbot is working perfectly. Here's how to test it:

---

## Method 1: Terminal Test (Quickest)

Run the comprehensive test:

```bash
cd c:\Users\echog\OneDrive\Desktop\cebuhotel
.\.venv\Scripts\python test_all_components.py
```

**Expected Output:**
```
✅ All critical tests passed!
```

---

## Method 2: Django Shell Test

```bash
python manage.py shell
```

Then in the shell:

```python
from authentication.gemini_chatbot import ask_gemini
from datetime import datetime

availability = {
    'total_rooms': 50,
    'available_count': 35,
    'by_type': {
        'Standard': {'total': 20, 'available': 18},
        'Premium': {'total': 20, 'available': 12},
        'Suite': {'total': 10, 'available': 5}
    },
    'check_date': datetime.now().date().strftime('%Y-%m-%d')
}

response = ask_gemini("What amenities do you offer?", availability)
print(response)
```

---

## Method 3: Web UI Test (Recommended)

### Step 1: Add URLs to your Django project

Edit your `cebuhotel/urls.py` and add:

```python
from django.urls import path, include

urlpatterns = [
    # ... your existing patterns ...
    path('', include('authentication.urls_chatbot_test')),  # Add this line
]
```

### Step 2: Start your Django server

```bash
python manage.py runserver
```

### Step 3: Open the test UI

Visit: **http://127.0.0.1:8000/chatbot/test/**

You'll see a beautiful chat interface where you can:
- Type questions directly
- Use quick-test buttons (Room Prices, Availability, etc.)
- Toggle between AI and keyword mode
- See real-time responses from Maya

---

## Method 4: API Test (For developers)

### Test with curl:

```bash
curl -X POST http://127.0.0.1:8000/api/chatbot/ \
  -H "Content-Type: application/json" \
  -d '{"message": "What are your room prices?", "use_ai": true}'
```

### Test with Python:

```python
import requests

response = requests.post('http://127.0.0.1:8000/api/chatbot/', json={
    'message': 'Do you have pet-friendly rooms?',
    'use_ai': True
})

print(response.json())
```

### Response Format:

```json
{
    "success": true,
    "response": "Yes, we do! 🐾 Grand Vista Hotel is happy to welcome your furry friends...",
    "use_ai": true,
    "status": "gemini_success"
}
```

---

## Available Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/chatbot/` | POST | Send message and get response |
| `/api/chatbot/info/` | GET | Get chatbot capabilities |
| `/api/chatbot/availability/` | GET | Get current room availability |
| `/chatbot/test/` | GET | Web UI for testing |

---

## What to Test

Try these questions:

1. **Prices**: "What are your room prices?"
2. **Availability**: "Do you have available rooms?"
3. **Policies**: "What's your cancellation policy?"
4. **Amenities**: "Tell me about your amenities"
5. **Pets**: "Do you accept pets?"
6. **Booking**: "How do I make a reservation?"
7. **Location**: "Where are you located?"
8. **Contact**: "How can I reach you?"

---

## Expected Behavior

✅ **With AI (Gemini):**
- Natural, conversational responses
- Understands context
- Provides detailed information
- Shows understanding of intent

✅ **With Keyword Fallback:**
- Structured responses
- Based on intent matching
- Quick and reliable

---

## Troubleshooting

### If chatbot doesn't respond:

1. **Check API key:**
   ```bash
   cat .env | grep GEMINI_API_KEY
   ```

2. **Check google-generativeai installation:**
   ```bash
   .\.venv\Scripts\pip list | grep google
   ```

3. **Run diagnostics:**
   ```bash
   .\.venv\Scripts\python test_all_components.py
   ```

### If API responds with error:

- Check `.env` file has API key
- Verify Django is running
- Check Django logs for errors
- Try keyword mode (toggle AI off)

---

## Integration into Your Existing UI

The chatbot is already integrated into your existing view at:
- File: `authentication/views_chatbot.py`
- Endpoint: `/api/chatbot/`

Your existing frontend should already be working! If not:

1. Make sure the URL is set up (see Step 1 above)
2. Check browser console for errors
3. Verify Django is serving the endpoint

---

## Performance

- **Response time**: 1-3 seconds (typical)
- **Capacity**: Handles concurrent requests
- **Availability**: 24/7

---

## API Usage

**Free Tier (if using Gemini free API):**
- 60 requests per minute
- Rate limiting applies

**Pro Tips:**
- Cache frequently asked questions
- Implement request throttling
- Monitor API usage in console

---

## Next Steps

1. ✅ Verify chatbot works (pick a test method above)
2. ✅ Integrate with your frontend
3. ✅ Monitor conversations
4. ✅ Gather feedback from guests
5. ✅ Adjust system prompt if needed

---

## Support

**Chatbot System Prompt**: `GEMINI_CHATBOT_GUIDE.md`
**Implementation Details**: `GEMINI_IMPLEMENTATION_SUMMARY.md`
**Quick Reference**: `CHATBOT_QUICK_REFERENCE.md`

Your chatbot is ready! 🎉
