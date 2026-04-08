# Simple FAQ Chatbot - Quick Start

## ✨ What's New

The hotel now features a **24/7 AI-powered FAQ Chatbot** in the bottom-right corner of every page!

### Key Features:
- 🤖 Instant answers to common questions
- 💬 Natural language processing (keyword-based)
- 📊 Live data from database
- 📱 Works on all devices
- 🎨 Sleek purple chat interface
- ⚡ AJAX-powered (no page reload)

---

## 🚀 Quick Start

### For Users

**Step 1: Find the Chat Box**
- Look bottom-right corner of any page
- Purple box with "Hotel Assistant" header
- Click to open if minimized

**Step 2: Ask Your Question**
- Type naturally in the input box
- Examples:
  - "What are your room prices?"
  - "Do you have any rooms available?"
  - "How do I book?"
  - "What's your check-in time?"
  - "Can I cancel my booking?"

**Step 3: Get Instant Answer**
- Bot responds with relevant, formatted information
- All data pulled from database (real-time)
- Can continue asking follow-up questions

**Type "help"** to see all capabilities!

### For Developers

**Installation:**
```bash
# Already included in project
# Just make sure base.html includes: {% include 'chatbot/chatbot_widget.html' %}
```

**Access API:**
```bash
# Send message to chatbot
curl -X POST /chatbot/api/response/ \
  -H "Content-Type: application/json" \
  -d '{"message":"What are your room prices?"}'

# Get chatbot info
curl -X GET /chatbot/api/info/
```

**Test in Django Shell:**
```bash
python manage.py shell
>>> from authentication.chatbot_engine import ChatbotEngine
>>> chatbot = ChatbotEngine()
>>> result = chatbot.process_message("What are your room prices?")
>>> print(result['response'])
```

---

## 📁 File Structure

```
New Files Created:
├── authentication/chatbot_engine.py       # Core logic (300+ lines)
├── authentication/views_chatbot.py        # AJAX endpoints (50+ lines)
├── authentication/urls_chatbot.py         # URL routing (8 lines)
└── templates/chatbot/
    └── chatbot_widget.html               # Chat widget UI (400+ lines)

Updated Files:
├── cebuhotel/urls.py                     # Added chatbot routes
└── templates/base.html                   # Added widget include
```

---

## 🧠 What the Chatbot Can Help With

| Topic | Example Questions |
|-------|-------------------|
| **💰 Prices** | "What are your room prices?" "How much do deluxe rooms cost?" |
| **📅 Availability** | "Do you have rooms available?" "How many rooms left?" |
| **📚 Booking** | "How do I book?" "What are the booking steps?" |
| **⏰ Check-in/Out** | "When is check-in?" "Check-out time?" |
| **🔄 Cancellation** | "Can I cancel?" "What's your cancellation policy?" |
| **🛏️ Rooms** | "What amenities?" "Room types?" "Capacity?" |
| **📍 Location** | "Where are you?" "How to get there?" |
| **📞 Contact** | "How to contact you?" "Phone number?" |

---

## 🔧 How It Works

### Intent-Based Matching
1. User types: "What are your room prices?"
2. System analyzes keywords: price, room, cost
3. Identifies intent: "room_price"
4. Queries database: Gets all rooms grouped by type
5. Formats response with current prices
6. Sends back in chat

### Dynamic Responses
**NOT**: Static text like "We have rooms available"
**BUT**: Real-time queries
- Current room availability
- Live pricing from database
- Real cancellation policies
- Actual contact information

---

## 💻 API Endpoints

### Send Message
```
POST /chatbot/api/response/
Content-Type: application/json

{
  "message": "What are your room prices?"
}

Response:
{
  "success": true,
  "response": "Here are our room prices:\n\n• Deluxe: ₱3,000/night...",
  "intent": "room_price",
  "confidence": 0.95
}
```

### Get Info
```
GET /chatbot/api/info/

Response:
{
  "name": "Hotel Assistant",
  "capabilities": ["Room prices", "Availability", ...],
  "available_24_7": true
}
```

---

## 🎨 Customization

### Change Chat Color
Edit `templates/chatbot/chatbot_widget.html` (line ~90):
```css
background: linear-gradient(135deg, #FF6B6B 0%, #FF6B6B 100%);  /* Red */
```

### Change Chat Position
Edit `templates/chatbot/chatbot_widget.html` (line ~45):
```css
bottom: 30px;  /* Distance from bottom */
right: 30px;   /* Distance from right */
```

### Add New Intent
Edit `authentication/chatbot_engine.py`:

**1. Add keywords:**
```python
'special_offers': ['offer', 'discount', 'promo', 'deal'],
```

**2. Create handler:**
```python
def get_special_offers_response(self, message):
    response = "Current offers:\n\n"
    offers = SpecialOffer.objects.filter(active=True)
    for offer in offers:
        response += f"• {offer.name}: {offer.description}\n"
    return response
```

**3. Add to routing:**
```python
intent_handlers = {
    'special_offers': self.get_special_offers_response,
}
```

---

## 🧪 Testing

### Manual Testing

**Test 1: Basic Questions**
1. Open `/rooms/`
2. Ask: "What are your room prices?"
3. Should show current prices grouped by type

**Test 2: Availability**
1. Ask: "Do you have availability?"
2. Should show today's available rooms
3. Numbers should match bookings in database

**Test 3: Intent Detection**
1. Ask: "How do I book a room?"
2. Should show booking steps

**Test 4: Mobile Responsive**
1. Test on phone/tablet
2. Chat box should fit properly
3. Text should be readable

### Automated Testing
```bash
# In Django shell
from authentication.chatbot_engine import ChatbotEngine

chatbot = ChatbotEngine()

# Test intent detection
intent, score = chatbot.detect_intent("What are your prices?")
print(f"Intent: {intent}, Score: {score:.2%}")  # Should be ~room_price

# Test response generation
result = chatbot.process_message("Do you have rooms?")
print(result['response'])  # Should show availability
```

---

## 🐛 Troubleshooting

**Q: Chat box not showing?**
- A: Check if `{% include 'chatbot/chatbot_widget.html' %}` is in base.html
- A: Check browser console for JavaScript errors

**Q: Responses not loading?**
- A: Check network tab → `/chatbot/api/response/` should return data
- A: Verify Django server is running

**Q: Same response every time?**
- A: Check if database queries are working
- A: Verify Room/Booking models have data

**Q: Bot says "unknown" to valid questions?**
- A: Add keywords to INTENT_KEYWORDS
- A: Try rephrasing question

---

## 📊 Monitoring

### View Chatbot Activity
```python
# In Django shell
from authentication.models import Room, Booking
from datetime import datetime, timedelta

# Check room count
print(f"Total rooms: {Room.objects.count()}")

# Check today's bookings
today = datetime.now().date()
bookings = Booking.objects.filter(
    check_in__lte=today,
    check_out__gt=today,
    status='CONFIRMED'
).count()
print(f"Today's bookings: {bookings}")
```

---

## ✅ Production Checklist

- [ ] Test chatbot on production database
- [ ] Verify CSRF token handling
- [ ] Test on mobile devices
- [ ] Test on different browsers
- [ ] Monitor performance (load time < 200ms)
- [ ] Check for typos in responses
- [ ] Verify all links work
- [ ] Test with high volume (rate limiting)
- [ ] Monitor error logs
- [ ] Gather user feedback

---

## 🎯 Next Steps

1. **Test thoroughly** with production data
2. **Monitor** chatbot conversations (optional: add logging)
3. **Gather feedback** from users
4. **Optimize** based on common questions
5. **Expand** with new intents based on user questions

---

**Feature Status**: ✅ Production Ready
**Version**: 1.0 (Phase 7)
**Last Updated**: 2024
