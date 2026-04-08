# Smart Room Recommendation System - User & Developer Guide

## 📋 Table of Contents
1. [Feature Overview](#feature-overview)
2. [User Guide](#user-guide)
3. [How Recommendations Work](#how-recommendations-work)
4. [Technical Architecture](#technical-architecture)
5. [API Documentation](#api-documentation)
6. [Customization Guide](#customization-guide)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Feature Overview

The Smart Room Recommendation System personalizes the booking experience by analyzing each guest's booking history and suggesting rooms that match their preferences.

### Key Features:
- **Personalized Recommendations**: Based on actual booking history
- **Similarity Scoring**: Uses weighted algorithm to match room preferences
- **Data-Driven**: Uses pandas for real-time analysis (not hardcoded)
- **Multi-Channel Display**: Shows recommendations on room list, booking confirmation, and booking detail pages
- **User Profile Analytics**: Displays personalized insights about booking patterns
- **Fallback System**: Suggests popular rooms for new users with no booking history

### Where Recommendations Appear:
1. **Room List Page** (`/rooms/`) - 3 recommended rooms widget
2. **Booking Confirmation Page** (`/bookings/confirm/<id>/`) - Alternative room options
3. **Booking Detail Page** (`/bookings/detail/<id>/`) - Similar rooms for future reference
4. **User Profile Page** (`/recommendations/profile/`) - Full booking history and insights
5. **Recommendations Page** (`/recommendations/all/`) - All recommendations with detailed matching scores

---

## 👥 User Guide

### Viewing Recommendations

#### 1. **Room List Page**
- Browse the main room selection page at `/rooms/`
- Scroll down to see "Recommended for You" section
- Shows up to 3 personalized room suggestions
- Each card displays:
  - Match score (%)
  - Room type & popularity badge
  - Price per night
  - Capacity
  - Why it was recommended
  - Booking count

#### 2. **Booking Confirmation**
- When confirming a booking, see alternatives in "You Might Also Like" section
- Helps users explore other options before finalizing
- Same information as room list recommendations
- Excludes the currently selected room

#### 3. **Booking Detail Page**
- View past bookings at `/bookings/history/`
- Click on any booking to see full details
- "Other Rooms You Might Like" section suggests alternatives
- Useful for planning future stays

#### 4. **User Profile**
- Visit `/recommendations/profile/` to see your booking profile
- View statistics:
  - Total bookings made
  - Total amount spent
  - Average stay duration
  - Average price per night
- See your booking preferences analysis:
  - Favorite room type
  - Most common price range
  - Typical stay length

#### 5. **All Recommendations**
- Visit `/recommendations/all/` for complete recommendation list
- View all recommended rooms at once
- See detailed match scores for each recommendation
- Profile summary shows your preference patterns

### Navigation
Use the navbar to access recommendations:
1. Click on **Recommendations** dropdown menu (between "My Bookings" and Admin)
2. Choose:
   - **My Profile**: View your booking analytics
   - **All Recommendations**: See all personalized suggestions

---

## 🧠 How Recommendations Work

### Recommendation Algorithm

The system uses a **weighted scoring algorithm** that analyzes your booking history and calculates similarity scores for each available room.

#### Scoring Breakdown:
- **40% Room Type Match**: Rooms matching your favorite type or similar categories
- **40% Price Match**: Rooms within your typical price range (±30% variance)
- **20% Capacity Match**: Rooms suitable for your typical group size

#### Example Calculation:
```
User Profile:
- Favorite Room Type: Deluxe
- Average Price per Night: ₱3,000
- Typical Capacity: 2 guests

Room A (Deluxe, ₱3,100, 2 guests):
- Type Match: 100% (exact match)
- Price Match: 96% (₱3,100 vs ₱3,000)
- Capacity Match: 100% (perfect for 2)
- Final Score: (100×0.4) + (96×0.4) + (100×0.2) = 98%

Room B (Suite, ₱4,500, 4 guests):
- Type Match: 70% (similar but not favorite)
- Price Match: 50% (outside typical range)
- Capacity Match: 60% (larger than needed)
- Final Score: (70×0.4) + (50×0.4) + (60×0.2) = 62%
```

### User Profile Analysis

The system tracks:
- **Favorite Room Type**: Most frequently booked room category
- **Price Range**: Minimum and maximum prices from bookings
- **Average Price**: Mean price per night across all bookings
- **Stay Duration**: Average number of nights per booking
- **Total Bookings**: Complete booking history count
- **Total Spent**: Lifetime spending at the hotel
- **Room Type Variations**: All room types ever booked

### Fallback System

**For New Users** (no booking history):
- System recommends the most popular rooms
- Based on booking frequency across all users
- Helps new guests find well-reviewed rooms
- Once user makes 1+ bookings, personalized recommendations activate

---

## 🏗️ Technical Architecture

### File Structure
```
authentication/
├── recommendation_engine.py      # Core recommendation logic
├── views_recommendations.py      # HTTP endpoints
├── urls_recommendations.py       # URL routing
├── views_bookings.py             # Updated booking views
└── views_rooms.py                # Updated room listing view

templates/
├── base.html                     # Updated navbar
├── rooms/
│   └── room_list.html           # Updated with recommendations
├── bookings/
│   ├── confirm_booking.html     # Updated with recommendations
│   └── booking_detail.html      # Updated with recommendations
└── recommendations/
    ├── recommendations_widget.html    # Reusable component
    ├── recommendations.html           # Full recommendations page
    └── user_profile.html             # User profile page

urls.py                           # Updated main URLs
```

### Key Components

#### 1. **RoomRecommendationEngine** (`recommendation_engine.py`)
- **Purpose**: Core recommendation logic
- **Main Methods**:
  - `__init__(user)`: Initialize with user object
  - `get_user_profile()`: Extract user's booking preferences
  - `calculate_similarity_score(room, user_profile)`: Score matching
  - `get_recommendations(exclude_room_id, limit)`: Generate recommendations
  - `get_recommendations_with_details()`: Enhanced output with explanations

#### 2. **View Functions** (`views_recommendations.py`)
- `get_user_recommendations()`: JSON API for AJAX requests
- `user_booking_profile()`: User profile page view
- `room_recommendations_page()`: Dedicated recommendations page
- `get_recommendations_context()`: Helper for template inclusion

#### 3. **Templates**
- `recommendations_widget.html`: Reusable recommendation card component
- `user_profile.html`: User's booking profile with statistics
- `recommendations.html`: Full recommendations page with grid layout

### Database Queries

**Minimal Database Impact:**
- Queries booking history once per recommendation request
- Uses Django ORM annotations for efficiency
- Caching potential: Could cache user profiles for 1-2 hours

**Related Models:**
- `Booking`: Guest's booking history
- `Room`: Available room inventory
- `BookingStatus`: Booking confirmation status
- `User`: Guest profile and authentication

---

## 📡 API Documentation

### JSON API Endpoint

**Endpoint**: `/recommendations/api/recommendations/`
**Method**: GET
**Authentication**: Required (Login)
**Parameters**:
- `exclude_room_id` (optional): Room ID to exclude (e.g., current booking)
- `limit` (optional): Number of recommendations (default: 3, max: 10)

**Request Example**:
```
GET /recommendations/api/recommendations/?exclude_room_id=5&limit=3
```

**Response Example**:
```json
{
  "success": true,
  "recommendations": [
    {
      "room_id": 12,
      "room_number": "305",
      "room_type": "Deluxe",
      "price_per_night": 3100,
      "capacity": 2,
      "match_score": 98,
      "reason": "Your favorite room type at a similar price",
      "booking_count": 245,
      "image_url": "/media/room_12.jpg"
    },
    {
      "room_id": 15,
      "room_number": "308",
      "room_type": "Premium",
      "price_per_night": 3500,
      "capacity": 2,
      "match_score": 87,
      "reason": "Similar price range as your previous bookings",
      "booking_count": 189,
      "image_url": "/media/room_15.jpg"
    }
  ],
  "user_profile": {
    "total_bookings": 5,
    "total_spent": 15000,
    "average_price": 3000,
    "average_duration": 3,
    "favorite_room_type": "Deluxe"
  }
}
```

### Template Context

**Room List View**:
```python
context = {
    'rooms': rooms,
    'recommendations': recommendations_list,
    'has_recommendations': bool(recommendations_list),
}
```

**Booking Confirmation View**:
```python
context = {
    'room': room,
    'check_in': check_in,
    'check_out': check_out,
    'recommendations': recommendations_list,
    'has_recommendations': bool(recommendations_list),
}
```

**Booking Detail View**:
```python
context = {
    'booking': booking,
    'recommendations': recommendations_list,
    'has_recommendations': bool(recommendations_list),
}
```

---

## 🛠️ Customization Guide

### 1. Adjusting Recommendation Algorithm Weights

**File**: `authentication/recommendation_engine.py` (lines ~150-180)

Current weights:
```python
ROOM_TYPE_WEIGHT = 0.40    # 40% importance
PRICE_WEIGHT = 0.40        # 40% importance
CAPACITY_WEIGHT = 0.20     # 20% importance
```

**To Change**:
```python
# Example: Emphasize price more, less emphasis on room type
ROOM_TYPE_WEIGHT = 0.30    # 30% importance
PRICE_WEIGHT = 0.50        # 50% importance
CAPACITY_WEIGHT = 0.20     # 20% importance
# Must sum to 1.0
```

### 2. Changing Price Tolerance Range

**File**: `authentication/recommendation_engine.py` (line ~160)

Current tolerance: ±30%
```python
PRICE_TOLERANCE = 0.30  # 30% variance allowed
```

**To Change**:
```python
PRICE_TOLERANCE = 0.20  # ±20% variance (stricter)
PRICE_TOLERANCE = 0.50  # ±50% variance (more lenient)
```

### 3. Changing Number of Recommendations

**Default**: 3 recommendations per location

**To Customize**:

**Room List** - `authentication/views_rooms.py`:
```python
recommendations_context = get_recommendations_context(request, limit=5)  # Changed from 3 to 5
```

**Booking Confirmation** - `authentication/views_bookings.py`:
```python
recommendations_context = get_recommendations_context(request, limit=4)  # Show 4 instead of 3
```

**Booking Detail** - `authentication/views_bookings.py`:
```python
recommendations_context = get_recommendations_context(request, limit=2)  # Show 2 instead of 3
```

### 4. Adding New Recommendation Factors

**File**: `authentication/recommendation_engine.py`

**Example: Add Amenities Matching**

```python
def calculate_similarity_score(self, room, user_profile):
    """Calculate similarity score with amenities preference"""
    
    # Existing scores
    room_type_score = self._calculate_room_type_match(room, user_profile)
    price_score = self._calculate_price_match(room, user_profile)
    capacity_score = self._calculate_capacity_match(room, user_profile)
    
    # NEW: Amenities score
    amenities_score = self._calculate_amenities_match(room, user_profile)
    
    # NEW weights (must sum to 1.0)
    ROOM_TYPE_WEIGHT = 0.35
    PRICE_WEIGHT = 0.35
    CAPACITY_WEIGHT = 0.15
    AMENITIES_WEIGHT = 0.15  # New
    
    score = (room_type_score * ROOM_TYPE_WEIGHT +
             price_score * PRICE_WEIGHT +
             capacity_score * CAPACITY_WEIGHT +
             amenities_score * AMENITIES_WEIGHT)
    
    return score

def _calculate_amenities_match(self, room, user_profile):
    """Calculate amenities preference match"""
    # Implementation
```

### 5. Customizing Recommendation Display

**Widget Template** - `templates/recommendations/recommendations_widget.html`

Change card styling:
```html
<!-- Line ~30: Change card colors -->
<div class="card border-success">  <!-- Changed from border-primary -->
    <div class="card-header bg-success">  <!-- Changed from bg-primary -->
```

Change information displayed:
```html
<!-- Add new fields -->
<p class="card-text">
    <strong>WiFi Speed:</strong> {{ room.wifi_speed }}
</p>
```

---

## 🐛 Troubleshooting

### Issue 1: No Recommendations Show

**Problem**: Recommendations section shows but with no rooms

**Solutions**:
1. **Check User Has Bookings**: User needs at least 1 completed booking
   - For new users, the fallback shows popular rooms instead
2. **Verify Available Rooms**: Ensure rooms exist in the database
   - Check Django admin: `/admin/authentication/room/`
3. **Check View Rendering**: Ensure `has_recommendations` context is passed
   - Look for: `{% if has_recommendations %}` in template

**Debug Steps**:
```python
# In views_bookings.py or views_rooms.py
recommendations_context = get_recommendations_context(request)
print("Recommendations:", recommendations_context)  # Check output
```

### Issue 2: Recommendation Scores Seem Wrong

**Problem**: Scores are too high, too low, or inconsistent

**Solutions**:
1. **Review Algorithm Weights**: Ensure they sum to 1.0
2. **Check User Profile**: Verify booking history is being analyzed correctly
3. **Clear Cache**: Django cache might have stale data

**Debug Steps**:
```python
# In your Django shell
from authentication.models import User
from authentication.recommendation_engine import RoomRecommendationEngine

user = User.objects.get(username='testuser')
engine = RoomRecommendationEngine(user)

# Check profile
profile = engine.get_user_profile()
print("Profile:", profile)

# Check recommendations
recs = engine.get_recommendations_with_details()
print("Recommendations:", recs)
```

### Issue 3: Performance Issues

**Problem**: Recommendations take too long to load

**Solutions**:
1. **Implement Caching**: Add Redis/Memcached
2. **Limit Database Queries**: Use `select_related()` / `prefetch_related()`
3. **Reduce Recommendation Limit**: Show fewer recommendations

**Optimization Code**:
```python
# In recommendation_engine.py
from django.db.models import Prefetch, Count

# Optimize queries
bookings = Booking.objects.filter(
    guest=self.user,
    status='CONFIRMED'
).select_related('room')
```

### Issue 4: Recommendations Not Updating

**Problem**: Same recommendations shown even after new bookings

**Solutions**:
1. **Clear Cache**: User cache might be outdated
2. **Check Booking Status**: Only CONFIRMED bookings are counted
3. **Refresh Page**: Hard refresh (Ctrl+Shift+R) to clear browser cache

---

## 📊 Analytics

### Tracking Recommendation Usage

The system tracks:
- Which rooms are recommended most
- Which recommendations are acted upon
- Average match scores
- User engagement with recommendations

**Potential Enhancements**:
- Add recommendation click tracking
- Calculate conversion rate (recommendation → booking)
- A/B test different algorithms
- ML-based algorithm improvement

### Sample Analytics Query

```python
# Count how often each room is recommended
from django.db.models import Count

room_recommendations = Room.objects.annotate(
    rec_count=Count('id')
).order_by('-rec_count')
```

---

## 🔐 Security Considerations

### Access Control
- ✅ All recommendation endpoints require login
- ✅ Users can only see their own recommendations
- ✅ Admin can view system-wide statistics

### Data Privacy
- ✅ Booking history is private to user
- ✅ User profile data not exposed via API
- ✅ Recommendations only visible to logged-in user

### Validation
- ✅ Input validation on all parameters
- ✅ Rate limiting recommended on API endpoint
- ✅ CSRF protection on all POST endpoints

---

## 📈 Future Enhancements

1. **Machine Learning Integration**
   - Use scikit-learn for more sophisticated algorithms
   - Train collaborative filtering model
   - Implement content-based recommendation

2. **Advanced Analytics**
   - Track recommendation acceptance rate
   - Measure ROI of recommendations
   - A/B test different algorithms

3. **Personalization**
   - Seasonal recommendations
   - Time-of-stay recommendations
   - Group size-based recommendations

4. **Performance**
   - Implement caching (Redis)
   - Pre-compute recommendations daily
   - Optimize database queries

5. **User Experience**
   - Interactive recommendation reasons
   - Recommendation feedback ("Was this helpful?")
   - Custom recommendation preferences

---

## 📞 Support

For issues or questions:
1. Check troubleshooting section above
2. Review code comments in `recommendation_engine.py`
3. Check Django logs: `logs/django.log`
4. Contact development team

---

**Last Updated**: 2024
**Version**: 1.0 (Phase 6)
**Status**: Production Ready
