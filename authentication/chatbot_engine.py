"""
Simple FAQ Chatbot Engine
Keyword-based intent matching for hotel inquiries
Pulls dynamic data from database (not static text)

Gemini API Integration
Enhanced with AI-powered system prompts for natural conversations
"""

from authentication.models import Room, Booking, BookingStatus
from datetime import datetime, timedelta
import re
from typing import Dict, Any


def build_system_prompt(availability_data: Dict[str, Any]) -> str:
    """
    Build a comprehensive system prompt for Gemini API.
    
    This prompt establishes Echo's personality and responsibilities as a hotel assistant
    for Cebu Mini Hotel. It includes all necessary information about the hotel, policies,
    and operational guidelines.
    
    Args:
        availability_data: Dictionary containing current room availability information.
                          Should include keys like:
                          - 'total_rooms': int (total rooms in hotel)
                          - 'available_count': int (currently available rooms)
                          - 'by_type': dict (availability by room type)
                          - 'check_date': str (check-in date)
    
    Returns:
        str: Full system prompt for Gemini API
    """
    
    # Format availability information
    availability_text = _format_availability_data(availability_data)
    
    system_prompt = f"""You are Echo, a helpful and professional hotel assistant for Cebu Mini Hotel.

═══════════════════════════════════════════════════════════════════
ABOUT Cebu Mini Hotel
═══════════════════════════════════════════════════════════════════

📍 LOCATION & CONTACT
• Hotel Name: Cebu Mini Hotel
• Location: Cebu City, Philippines
• Phone: +63 32 412 3456 (24/7)
• 24-Hour Support: +63 917 123 4567
• Email: info@cebuminihotel.com
• Website: www.cebuminihotel.com

⏰ CHECK-IN & CHECK-OUT TIMES
• Check-in: 2:00 PM (Early check-in available upon request)
• Check-out: 11:00 AM
• Late check-out: Available for additional fee
  - Until Noon (11 AM - 1 PM): ₱500
  - Until 4 PM (11 AM - 4 PM): ₱800

═══════════════════════════════════════════════════════════════════
ROOM TYPES & PRICING
═══════════════════════════════════════════════════════════════════
"""
    
    # Add room information from database
    try:
        rooms = Room.objects.all().order_by('price_per_night')
        if rooms.exists():
            room_types = {}
            for room in rooms:
                room_type = room.get_room_type_display()
                if room_type not in room_types:
                    room_types[room_type] = {
                        'capacity': room.capacity,
                        'price': room.price_per_night,
                        'count': 0,
                        'amenities': room.amenities or 'Standard amenities'
                    }
                room_types[room_type]['count'] += 1
            
            for room_type in sorted(room_types.keys()):
                info = room_types[room_type]
                system_prompt += f"""
• {room_type}
  - Maximum Capacity: {info['capacity']} guests
  - Price: ₱{info['price']:,} per night
  - Total Rooms: {info['count']}
  - Features: {info['amenities']}"""
        else:
            system_prompt += "\n• Standard rooms with modern amenities"
    except Exception:
        system_prompt += "\n• Standard rooms with modern amenities"
    
    system_prompt += f"""

═══════════════════════════════════════════════════════════════════
AMENITIES & FACILITIES
═══════════════════════════════════════════════════════════════════

🏨 Hotel-Wide Amenities:
• 24/7 Front Desk Service
• Free Wi-Fi throughout the hotel
• Air-conditioned rooms and common areas
• Hot & Cold Water Supply
• Grocery/Convenience Store (24/7)
• Laundry & Dry Cleaning Service
• Room Service (7 AM - 11 PM)
• Complimentary Toiletries

🍽️ Dining & Beverage:
• In-house Restaurant (7 AM - 10 PM)
• Coffee Shop & Café
• Room Service Menu
• Breakfast Options Available

🏊 Recreation & Wellness:
• Swimming Pool
• Fitness Center / Gym
• Spa & Massage Services
• Business Center
• Meeting Rooms Available

🚗 Transportation & Parking:
• Free On-site Parking
• Airport Shuttle (₱500 per ride)
• 24-Hour Taxi Service Available
• Nearby Transportation: Grab, Uber

═══════════════════════════════════════════════════════════════════
POLICIES
═══════════════════════════════════════════════════════════════════

💳 PAYMENT METHODS ACCEPTED
• Credit Cards: Visa, Mastercard, American Express
• PayMongo (Local Philippine payment solutions)
• Bank Transfers
• Cash Payment at Front Desk
• E-wallet: GCash, PayPal

💰 CANCELLATION POLICY
• Free Cancellation: Cancel more than 48 hours before check-in for a full refund
• Non-Refundable: Cancel 48 hours or less before check-in
• No-Show: No refund
• Refund Processing Time: 5-7 business days after approval

🐕 PET POLICY
• Pets are welcome with prior notification
• Pet Fee: ₱500 per pet per night
• Pets must be well-behaved and crate-trained
• Pet owners are responsible for any damages
• Contact hotel 24 hours before arrival to register pets

📋 HOUSE RULES
• Quiet Hours: 10 PM - 8 AM
• No loud parties or excessive noise
• Smoking Only in Designated Areas
• No smoking in rooms (₱1,000 penalty)
• Maximum Occupancy: As per room type
• Guests must be 18+ to check in
• ID required at check-in

🔐 SECURITY & LIABILITY
• Hotel provides safety deposit boxes
• Valuables should be stored securely
• Hotel not responsible for lost or stolen items
• Security cameras in public areas only
• Room access card must not be shared

═══════════════════════════════════════════════════════════════════
CURRENT ROOM AVAILABILITY
═══════════════════════════════════════════════════════════════════

{availability_text}

═══════════════════════════════════════════════════════════════════
YOUR ROLE & GUIDELINES
═══════════════════════════════════════════════════════════════════

✅ YOUR RESPONSIBILITIES:
1. Answer questions about rooms, prices, and availability
2. Provide information about hotel policies and procedures
3. Help guests with booking inquiries and guidance
4. Offer room recommendations based on guest needs
5. Provide directions and local area information
6. Be warm, professional, and helpful at all times

⚠️ IMPORTANT RULES:
1. ONLY answer questions related to Cebu Mini Hotel
2. NEVER make up prices, policies, or information
3. NEVER confirm bookings (only guide guests to booking system)
4. If unsure about any information, respond exactly with:
   "I'm not certain about that detail. Let me connect you with our staff who can give you accurate information. Please reach out to +63 32 412 3456 or email info@cebuminihotel.com"
5. Stay professional and courteous at all times
6. Encourage guests to contact front desk for complex issues

🎯 CONVERSATION STYLE:
• Be friendly and approachable
• Use professional but warm language
• Keep answers compact: 2-5 short lines for simple questions, or up to 6 bullets for lists
• Put the direct answer first, then one helpful next step
• Use emojis sparingly, only when they make the answer easier to scan
• Ask clarifying questions when needed
• Provide enough detail to be useful without overwhelming the guest
• Suggest related services when appropriate
• Always be honest about limitations

❌ DO NOT:
• Accept or process payments
• Make or modify actual bookings
• Promise room features not listed
• Guarantee availability (use current data)
• Recommend competitor hotels
• Share personal information about guests
• Discuss sensitive business information

═══════════════════════════════════════════════════════════════════

Remember: Your goal is to provide excellent customer service and make guests feel welcome at Cebu Mini Hotel!
"""
    
    return system_prompt


def _format_availability_data(availability_data: Dict[str, Any]) -> str:
    """
    Helper function to format availability data into readable text.
    
    Args:
        availability_data: Dictionary with availability information
    
    Returns:
        str: Formatted availability information
    """
    if not availability_data:
        return "Please check back with us for current availability or call +63 32 412 3456"
    
    formatted = ""
    
    # Add total availability
    if 'available_count' in availability_data and 'total_rooms' in availability_data:
        total = availability_data['total_rooms']
        available = availability_data['available_count']
        formatted += f"✅ Quick View: {available} out of {total} rooms currently available\n"
    
    # Add check date if provided
    if 'check_date' in availability_data:
        formatted += f"📅 Check Date: {availability_data['check_date']}\n"
    
    # Add availability by room type
    if 'by_type' in availability_data and availability_data['by_type']:
        formatted += "\n🛏️ Availability by Room Type:\n"
        for room_type, count_info in availability_data['by_type'].items():
            if isinstance(count_info, dict):
                available = count_info.get('available', 0)
                total = count_info.get('total', 0)
                formatted += f"  • {room_type}: {available}/{total} available\n"
            else:
                # Simple count format
                formatted += f"  • {room_type}: {count_info} available\n"
    
    if not formatted:
        formatted = "Please contact us directly for availability: +63 32 412 3456"
    
    return formatted


class ChatbotEngine:
    """
    Simple FAQ chatbot for hotel inquiries
    Uses keyword matching to detect intent
    Pulls information from database dynamically
    """
    
    # Intent keywords - maps keywords to intent types
    INTENT_KEYWORDS = {
        'room_price': ['price', 'cost', 'how much', 'charge', 'rate', 'expensive', '$', '₱', 'rent', 'magkano', 'pila', 'presyo'],
        'room_availability': ['available', 'availability', 'available room', 'current availability', 'free room', 'vacant', 'open', 'left', 'have any', 'libre pa', 'may room pa', 'bakante', 'open pa'],
        'booking_steps': ['book', 'booking', 'how to book', 'reserve', 'reservation', 'step', 'process', 'mag book', 'mag reserve', 'gusto ko mag'],
        'check_in_out': ['check-in', 'check-out', 'check in', 'check out', 'time', 'arrival', 'departure'],
        'cancellation': ['cancel', 'cancellation', 'refund', 'policy', 'change', 'modify', 'i-cancel', 'kanselahin', 'icancelled'],
        'payment': ['payment', 'pay', 'paid', 'card', 'credit card', 'gcash', 'bank transfer', 'cash', 'paymongo', 'paypal', 'method', 'methods'],
        'terms_privacy': ['terms', 'conditions', 'privacy policy', 'privacy', 'data privacy', 'data', 'liability', 'guest rules', 'house rules', 'personal information'],
        'room_details': ['room', 'amenities', 'type', 'capacity', 'bed', 'feature', 'include', 'kwarto', 'silid', 'room nyo', 'mga room', 'rooms', 'types'],
        'contact': ['contact', 'phone', 'email', 'call', 'reach', 'support', 'number nyo', 'numero', 'address nyo'],
        'location': ['location', 'where', 'address', 'cebu'],
        'help': ['help', 'what can you do', 'commands', 'options', 'menu', 'kumusta', 'helo', 'maayong', 'ayo', 'kamusta'],
        'recommend': [
            'recommend', 'suggest', 'which room', 'best room', 
            'what room', 'help me choose', 'room for me', 
            'which one', 'what should i', 'budget', 'affordable',
            'luxury room', 'family room', 'couple', 'romantic',
            'honeymoon', 'anniversary', 'cheapest', 'most expensive',
            'irekomenda', 'anong room'
        ],
    }
    
    def __init__(self):
        self.name = "Echo"
        self.greeting_given = False
    
    def detect_intent(self, user_message):
        """
        Detect intent from user message using keyword matching
        Returns: (intent_name, confidence_score)
        """
        message_lower = user_message.lower()
        message_words = set(re.findall(r'\b\w+\b', message_lower))
        
        intent_scores = {}
        
        # Score each intent based on keyword matches
        for intent, keywords in self.INTENT_KEYWORDS.items():
            matches = sum(1 for keyword in keywords if keyword in message_lower)
            if matches > 0:
                intent_scores[intent] = matches
        
        if not intent_scores:
            return ('unknown', 0.0)
        
        # Get highest scoring intent
        best_intent = max(intent_scores.items(), key=lambda x: x[1])
        return (best_intent[0], min(best_intent[1] / 3, 1.0))  # Normalize confidence to 0-1
    
    def get_room_price_response(self, message):
        """Get response about room prices"""
        rooms = Room.objects.all().order_by('room_type', 'price_per_night')
        
        if not rooms:
            return "I couldn't load the room rates right now. Please try again or contact the front desk at +63 32 412 3456."
        
        # Group by room type
        price_by_type = {}
        for room in rooms:
            room_type = room.get_room_type_display()
            if room_type not in price_by_type:
                price_by_type[room_type] = []
            price_by_type[room_type].append(room.price_per_night)
        
        response = "**Current room rates**\n\n"
        for room_type in sorted(price_by_type.keys()):
            prices = price_by_type[room_type]
            min_price = min(prices)
            max_price = max(prices)
            
            if min_price == max_price:
                response += f"• **{room_type}**: ₱{min_price:,} per night\n"
            else:
                response += f"• **{room_type}**: ₱{min_price:,} - ₱{max_price:,} per night\n"
        
        response += "\nRates may change by date. Tell me your budget or travel date and I can help narrow the options."
        return response
    
    def get_availability_response(self, message):
        """Get response about available rooms"""
        # Get all rooms
        total_rooms = Room.objects.count()
        
        # Get booked rooms for today
        today = datetime.now().date()
        
        booked_today = set(Booking.objects.filter(
            check_in__lte=today,
            check_out__gt=today,
            status='CONFIRMED'
        ).values_list('room_id', flat=True))
        
        available_today = total_rooms - len(booked_today)
        
        rooms_by_type = {}
        for room in Room.objects.all():
            room_type = room.get_room_type_display()
            if room_type not in rooms_by_type:
                rooms_by_type[room_type] = {'total': 0, 'available': 0}
            rooms_by_type[room_type]['total'] += 1
            if room.id not in booked_today:
                rooms_by_type[room_type]['available'] += 1
        
        response = f"**Today's availability** ({today.strftime('%b %d, %Y')})\n\n"
        response += f"• **Total available**: {available_today}/{total_rooms} rooms\n"
        response += "• **By room type**:\n"
        
        for room_type in sorted(rooms_by_type.keys()):
            total = rooms_by_type[room_type]['total']
            available = rooms_by_type[room_type]['available']
            response += f"  - **{room_type}**: {available}/{total} available\n"
        
        response += "\nAvailability is live and can change quickly. For exact dates, start a booking or ask staff to confirm."
        return response
    
    def get_booking_steps_response(self, message):
        """Get response about booking process"""
        response = """**How to book**

1. Open the room list and choose a room.
2. Select your check-in and check-out dates.
3. Review the guest details, requests, and total price.
4. Confirm the booking and complete payment.

After payment, you'll receive your confirmation and booking reference. I can also recommend a room if you tell me your budget, group size, or occasion."""
        return response
    
    def get_check_in_out_response(self, message):
        """Get response about check-in/check-out times"""
        response = """**Check-in & Check-out Times** ⏰

**Check-in Time:** 2:00 PM
• Earliest check-in available on request (subject to availability)
• Early check-in fee may apply

**Check-out Time:** 11:00 AM
• Late check-out available for additional charge
• Late check-out subject to room availability

**Late Check-out Options:**
• Noon (11:00 AM - 1:00 PM): ₱500
• Evening (11:00 AM - 4:00 PM): ₱800
• Special arrangements available upon request

💡 **Tip:** Contact us at least 24 hours before arrival for early check-in arrangements.

Need help with anything else? 🏨"""
        return response
    
    def get_cancellation_response(self, message):
        """Get response about cancellation policy"""
        response = """**Cancellation Policy** 🔄

**Free Cancellation:**
• Cancel more than 48 hours before check-in
• Full refund after approval

**Non-Refundable:**
• Cancel 48 hours or less before check-in: No refund
• No-show: No refund
• Special promo, discounted, or event bookings may have separate refund terms

**How to Cancel:**
1. Go to "My Bookings" in your account
2. Select the booking you want to cancel
3. Click "Cancel Booking"
4. Confirm cancellation
5. Approved refunds are processed within 5-7 business days

**Need to Change Dates?**
• You can modify your booking up to 7 days before check-in
• Any price difference will be adjusted

Have questions? Contact us anytime! 📞"""
        return response

    def get_payment_response(self, message):
        """Get response about accepted payment methods"""
        response = """**Payment methods**

We accept:
• Credit and debit cards
• GCash and PayMongo-supported local payments
• Bank transfer
• PayPal
• Cash at the front desk

For online bookings, follow the payment step after confirming your room and dates."""
        return response

    def get_terms_privacy_response(self, message):
        """Get response about terms, privacy, and guest rules"""
        response = """**Terms and privacy**

Our terms cover booking changes, payments, check-in, guest conduct, data privacy, and hotel liability.

Guest data is used for booking, payment, service, and support purposes. For a specific concern, review the terms page or contact support@cebuhotel.com."""
        return response
    
    def get_room_details_response(self, message):
        """Get response about room types and features"""
        rooms = Room.objects.all()
        
        if not rooms:
            return "Sorry, I couldn't find any room information."
        
        # Group by type and get details
        room_types = {}
        for room in rooms:
            room_type = room.get_room_type_display()
            if room_type not in room_types:
                room_types[room_type] = {
                    'count': 0,
                    'capacity': room.capacity,
                    'price': room.price_per_night,
                    'amenities': room.amenities or 'N/A'
                }
            room_types[room_type]['count'] += 1
        
        response = "**Our Room Types** 🛏️\n\n"
        
        for room_type in sorted(room_types.keys()):
            info = room_types[room_type]
            response += f"**{room_type}**\n"
            response += f"• Capacity: {info['capacity']} guests\n"
            response += f"• Price: ₱{info['price']:,}/night\n"
            response += f"• Available: {info['count']} rooms\n"
            
            if info['amenities'] != 'N/A':
                amenities = info['amenities'].split(',')
                response += f"• Amenities: {', '.join(amenities[:3])}\n"
            
            response += "\n"
        
        response += "Want to book or need more details? 😊"
        return response
    
    def get_contact_response(self, message):
        """Get contact information"""
        response = """**Contact Us** 📞

We'd love to hear from you!

**Phone:**
• Main: +63 2 1234 5678
• 24/7 Support: +63 917 123 4567

**Email:**
• General Inquiries: info@cebuhotel.com
• Support: support@cebuhotel.com
• Bookings: bookings@cebuhotel.com

**Address:**
Cebu Hotel
Cebu City, Philippines

**Hours:**
• Reservations: 24/7
• Front Desk: 24/7
• Support: 24/7

**Online:**
• Live Chat: Available 24/7 on website
• Email Response: Within 2 hours

Looking forward to helping you! 🏨"""
        return response
    
    def get_location_response(self, message):
        """Get location information"""
        response = """**Our Location** 📍

**Cebu Hotel**
Cebu City, Philippines

**Getting Here:**

✈️ **By Air:**
• Mactan-Cebu International Airport (30 mins by taxi)
• Complimentary airport shuttle available
• Book in advance at booking confirmation

🚕 **By Taxi/Ride-Share:**
• Grab or Uber: ~₱300-500 from airport
• Metered taxi available 24/7

🚗 **By Car:**
• Free parking available
• 10-minute drive from downtown Cebu

📍 **Nearby Attractions:**
• Cebu Taoist Temple: 15 mins
• IT Park: 20 mins
• Mactan Island: 30 mins
• Beaches: 20-40 mins

Need directions? I can help! 🗺️"""
        return response
    
    def get_help_response(self, message):
        """Get help about what the chatbot can do"""
        response = """**I can help with:**

• Room rates and availability
• Booking steps
• Check-in and check-out times
• Cancellation and refund policy
• Room types, capacity, and amenities
• Location and contact details
• Room recommendations

Try asking: "Recommend a room for two people" or "What payment methods do you accept?" """
        return response
    
    def _recommend_room(self, message: str) -> str:
        """
        Recommends a room based on budget or guest count keywords.
        Pulls live prices from the Room model.
        """
        message_lower = message.lower()

        # Pull rooms from DB ordered by price (include all rooms, regardless of availability flag)
        rooms = Room.objects.all().order_by('price_per_night')

        if not rooms.exists():
            return (
                "I'm unable to retrieve room information at the moment. "
                "Please contact our front desk at +63 32 412 3456."
            )

        # ── Budget detection ─────────────────────────────────
        if any(word in message_lower for word in 
               ['cheap', 'affordable', 'budget', 'lowest', 'cheapest', 'basic', 'pila', 'magkano']):
            room = rooms.first()  # cheapest available
            desc = room.description if room.description else "A wonderful room"
            return (
                f"For the best value, I'd recommend our **{room.get_room_type_display()}** "
                f"at ₱{room.price_per_night:,}/night. 🛏\n\n"
                f"{desc}\n\n"
                f"It offers everything you need for a comfortable and "
                f"refined stay. Shall I guide you through booking?"
            )

        # ── Luxury / special occasion detection ──────────────
        if any(word in message_lower for word in 
               ['luxury', 'best', 'suite', 'special', 'anniversary', 
                'honeymoon', 'vip', 'premium', 'top', 'pinakamahusay']):
            room = rooms.last()  # most expensive
            desc = room.description if room.description else "A wonderful room"
            return (
                f"For an extraordinary experience, our **{room.get_room_type_display()}** "
                f"at ₱{room.price_per_night:,}/night is our finest offering. ✨\n\n"
                f"{desc}\n\n"
                f"This is our most exclusive accommodation, "
                f"complete with premium amenities. Shall I help you reserve it?"
            )

        # ── Group / family detection ──────────────────────────
        if any(word in message_lower for word in 
               ['family', 'group', 'kids', 'children', 'large', 'spacious', 'pamilya']):
            spacious = rooms.filter(capacity__gte=3).order_by('capacity').first()
            if spacious:
                desc = spacious.description if spacious.description else "A wonderful room"
                return (
                    f"For groups or families, our **{spacious.get_room_type_display()}** "
                    f"is an excellent choice at ₱{spacious.price_per_night:,}/night. 👨‍👩‍👧\n\n"
                    f"{desc}\n\n"
                    f"It comfortably accommodates your group with ample space. "
                    f"Would you like to book this room?"
                )

        # ── Couple / romantic detection ───────────────────────
        if any(word in message_lower for word in 
               ['couple', 'romantic', 'date', 'partner', '2 people', 
                'two people', 'just two', 'duha']):
            mid = rooms[len(rooms) // 2] if len(rooms) > 1 else rooms.first()
            desc = mid.description if mid.description else "A wonderful room"
            return (
                f"For a romantic getaway, our **{mid.get_room_type_display()}** "
                f"at ₱{mid.price_per_night:,}/night would be perfect. 🌹\n\n"
                f"{desc}\n\n"
                f"An intimate and elegant choice for two. "
                f"Shall I walk you through the booking process?"
            )

        # ── Default: show all options ─────────────────────────
        response = "**Room recommendations**\n\n"
        for room in rooms[:5]:
            desc_preview = room.description[:80] if room.description else "A wonderful room"
            desc_preview = f"{desc_preview}..." if room.description else desc_preview
            response += (
                f"• **{room.get_room_type_display()}** (Room {room.room_number}) - ₱{room.price_per_night:,}/night\n"
                f"{desc_preview}\n\n"
            )
        response += (
            "Tell me your budget, guest count, or occasion and I can choose the best fit."
        )
        return response
    
    def get_unknown_response(self, message):
        """Get response for unknown queries"""
        response = """I'm not sure I understood that yet.

I can help with room rates, availability, booking steps, payments, cancellation rules, room recommendations, and contact details.

Try asking: "What rooms are available today?" or "How do I book a room?" """
        return response
    
    def get_greeting_response(self):
        """Get greeting response"""
        response = """Hi, I'm **Echo**, your hotel assistant.

I can help with rooms, rates, availability, bookings, payments, cancellations, and contact details. What would you like to know?"""
        return response
    
    def process_message(self, user_message):
        """
        Process user message and return chatbot response
        Returns: dict with response and metadata
        """
        if not user_message or not user_message.strip():
            return {
                'response': "Please ask me something! 😊",
                'intent': 'empty',
                'confidence': 0.0,
            }
        
        user_message = user_message.strip()
        
        # Check for greeting
        if user_message.lower() in ['hi', 'hello', 'hey', 'start', 'hello there']:
            if not self.greeting_given:
                self.greeting_given = True
                return {
                    'response': self.get_greeting_response(),
                    'intent': 'greeting',
                    'confidence': 1.0,
                }
        
        # Check for help
        if user_message.lower() == 'help':
            return {
                'response': self.get_help_response(user_message),
                'intent': 'help',
                'confidence': 1.0,
            }
        
        # Detect intent
        intent, confidence = self.detect_intent(user_message)
        
        # Route to appropriate response
        intent_handlers = {
            'room_price': self.get_room_price_response,
            'room_availability': self.get_availability_response,
            'booking_steps': self.get_booking_steps_response,
            'check_in_out': self.get_check_in_out_response,
            'cancellation': self.get_cancellation_response,
            'payment': self.get_payment_response,
            'terms_privacy': self.get_terms_privacy_response,
            'room_details': self.get_room_details_response,
            'contact': self.get_contact_response,
            'location': self.get_location_response,
            'recommend': self._recommend_room,
            'help': self.get_help_response,
        }
        
        handler = intent_handlers.get(intent, self.get_unknown_response)
        response = handler(user_message)
        
        return {
            'response': response,
            'intent': intent,
            'confidence': confidence,
        }


def get_chatbot_response(message):
    """Convenience function to get chatbot response"""
    chatbot = ChatbotEngine()
    return chatbot.process_message(message)
