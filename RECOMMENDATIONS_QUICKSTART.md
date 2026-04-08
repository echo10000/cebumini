# Smart Room Recommendations - Quick Start

## ✨ What's New

The hotel now features a **Smart Room Recommendation System** that personalizes the booking experience!

### Key Highlights:
- 🎯 Personalized recommendations based on booking history
- 📊 Intelligent matching algorithm using pandas
- 🌍 Shows on room list, booking confirmation, and booking detail pages
- 👤 User profile page with booking analytics
- ⭐ Match scores explaining why each room was recommended

---

## 🚀 Quick Start

### For Users

**Step 1: Browse Rooms**
- Visit the room list at `/rooms/`
- If you have previous bookings, scroll down to see "Recommended for You"
- Each recommendation shows a match score (%) and explanation

**Step 2: Check Your Profile**
- Click "Recommendations" → "My Profile" in the navbar
- View your booking statistics and preferences
- See personalized insights

**Step 3: View All Recommendations**
- Click "Recommendations" → "All Recommendations" in the navbar
- See complete list with detailed match scores

**Step 4: Book & Discover**
- When confirming a booking, see alternative rooms in "You Might Also Like"
- After booking, view similar rooms on your booking detail page

### For Developers

**Installation:**
```bash
# pandas is already in requirements
pip install pandas numpy  # If not already installed

# Pandas may already be installed by Django dependencies
```

**Test the System:**
```bash
python manage.py shell < test_recommendations.py
```

**Access API Endpoint:**
```
GET /recommendations/api/recommendations/?exclude_room_id=5&limit=3
```

---

## 📁 File Structure

```
New Files Created:
├── authentication/recommendation_engine.py      # Core logic (380+ lines)
├── authentication/views_recommendations.py      # Views (80+ lines)
├── authentication/urls_recommendations.py       # URL routing (8 lines)
├── templates/recommendations/
│   ├── recommendations_widget.html             # Reusable component
│   ├── user_profile.html                       # Profile page
│   └── recommendations.html                    # Full recommendations page
├── test_recommendations.py                      # Test suite
└── RECOMMENDATIONS_GUIDE.md                     # Full documentation

Updated Files:
├── cebuhotel/urls.py                           # Added recommendations routes
├── authentication/views_rooms.py                # Room list integration
├── authentication/views_bookings.py             # Booking views integration
├── templates/base.html                          # Added navbar menu
├── templates/rooms/room_list.html               # Added widget
├── templates/bookings/confirm_booking.html      # Added recommendations
└── templates/bookings/booking_detail.html       # Added recommendations
```

---

## 🧮 How It Works

### Algorithm
The system scores each room on:
1. **Room Type Match (40%)** - Matches your favorite room type
2. **Price Match (40%)** - Similar to your typical spending
3. **Capacity Match (20%)** - Suitable for your group size

**Example:**
- You usually book Deluxe rooms for ₱3,000/night with 2 people
- Deluxe room at ₱3,100/night for 2 people = 98% match ⭐
- Suite room at ₱4,500/night for 4 people = 62% match

### Fallback
**New users with no bookings:**
- Shows the most popular rooms instead
- Once you book 1+ rooms, personalized recommendations activate

---

## 🔧 Customization

### Change Recommendation Count
Edit these files to show more/fewer recommendations:

**Room List** - `authentication/views_rooms.py`:
```python
get_recommendations_context(request, limit=3)  # Change 3 to desired number
```

**Booking Confirmation** - `authentication/views_bookings.py`:
```python
get_recommendations_context(request, limit=3)  # Adjust limit
```

### Adjust Algorithm Weights
Edit `authentication/recommendation_engine.py` (line ~160):
```python
ROOM_TYPE_WEIGHT = 0.40    # Change percentage
PRICE_WEIGHT = 0.40        # Must sum to 1.0
CAPACITY_WEIGHT = 0.20
```

### Change Price Tolerance
Edit `authentication/recommendation_engine.py` (line ~155):
```python
PRICE_TOLERANCE = 0.30  # ±30% variance (currently 30%)
```

---

## 📊 API Endpoint

### Get Recommendations (JSON)

**URL**: `/recommendations/api/recommendations/`
**Method**: GET
**Auth**: Login required

**Parameters:**
- `exclude_room_id` (optional): Skip a specific room
- `limit` (optional): Max recommendations (default: 3)

**Example:**
```bash
curl -X GET "/recommendations/api/recommendations/?exclude_room_id=5&limit=3" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "success": true,
  "recommendations": [
    {
      "room_id": 12,
      "room_number": "305",
      "room_type": "Deluxe",
      "price_per_night": 3100,
      "match_score": 98,
      "reason": "Your favorite room type at a similar price"
    }
  ],
  "user_profile": {
    "total_bookings": 5,
    "average_price": 3000,
    "favorite_room_type": "Deluxe"
  }
}
```

---

## 🧪 Testing

### Run Test Suite
```bash
python manage.py shell
>>> exec(open('test_recommendations.py').read())
```

### Manual Testing

**Test 1: New User Fallback**
1. Create new account
2. Visit `/rooms/` 
3. Should see popular rooms in recommendations

**Test 2: Personalized Recommendations**
1. Make 3-5 bookings of same room type
2. Visit `/rooms/`
3. Should see mostly that room type recommended

**Test 3: Price Matching**
1. Book rooms in ₱3,000-4,000 range
2. Visit recommendations
3. Should see mostly rooms in that price range

---

## 🐛 Troubleshooting

**Q: No recommendations showing?**
- A: You need at least 1 booking to see personalized recommendations
- New users see popular rooms instead

**Q: Same recommendations as before?**
- A: Hard refresh page (Ctrl+Shift+R) to clear cache

**Q: API returning error?**
- A: Make sure you're logged in
- Check user has at least 1 booking

**Q: Scores seem wrong?**
- A: Algorithm weights must sum to 1.0
- Review `RECOMMENDATIONS_GUIDE.md` for troubleshooting

---

## 📚 Full Documentation

See `RECOMMENDATIONS_GUIDE.md` for:
- Complete algorithm explanation with examples
- All customization options
- Full API documentation
- Advanced troubleshooting
- Future enhancement ideas

---

## 🎯 Next Steps

1. **Test the system** with real bookings
2. **Customize** algorithm weights if needed
3. **Monitor** which recommendations users click
4. **Gather feedback** for algorithm improvements

---

**Feature Status**: ✅ Production Ready
**Version**: 1.0 (Phase 6)
**Last Updated**: 2024
