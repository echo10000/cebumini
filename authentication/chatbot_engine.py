"""
Simple FAQ Chatbot Engine
Keyword-based intent matching for hotel inquiries
Pulls dynamic data from database (not static text)
"""

from authentication.models import Room, Booking, BookingStatus
from datetime import datetime, timedelta
import re


class ChatbotEngine:
    """
    Simple FAQ chatbot for hotel inquiries
    Uses keyword matching to detect intent
    Pulls information from database dynamically
    """
    
    # Intent keywords - maps keywords to intent types
    INTENT_KEYWORDS = {
        'room_price': ['price', 'cost', 'how much', 'charge', 'rate', 'expensive', '$', '₱', 'rent'],
        'room_availability': ['available', 'available room', 'free room', 'vacant', 'open', 'left', 'have any'],
        'booking_steps': ['book', 'booking', 'how to book', 'reserve', 'reservation', 'step', 'process'],
        'check_in_out': ['check-in', 'check-out', 'check in', 'check out', 'time', 'arrival', 'departure'],
        'cancellation': ['cancel', 'cancellation', 'refund', 'policy', 'change', 'modify'],
        'room_details': ['room', 'amenities', 'type', 'capacity', 'bed', 'feature', 'include'],
        'contact': ['contact', 'phone', 'email', 'call', 'reach', 'support'],
        'location': ['location', 'where', 'address', 'cebu'],
        'help': ['help', 'what can you do', 'commands', 'options', 'menu'],
    }
    
    def __init__(self):
        self.name = "Hotel Assistant"
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
            return "Sorry, I couldn't find any room information at the moment."
        
        # Group by room type
        price_by_type = {}
        for room in rooms:
            room_type = room.get_room_type_display()
            if room_type not in price_by_type:
                price_by_type[room_type] = []
            price_by_type[room_type].append(room.price_per_night)
        
        # Build response
        response = "Here are our room prices:\n\n"
        for room_type in sorted(price_by_type.keys()):
            prices = price_by_type[room_type]
            min_price = min(prices)
            max_price = max(prices)
            
            if min_price == max_price:
                response += f"• **{room_type}**: ₱{min_price:,} per night\n"
            else:
                response += f"• **{room_type}**: ₱{min_price:,} - ₱{max_price:,} per night\n"
        
        response += "\nWould you like to book a room? 🏨"
        return response
    
    def get_availability_response(self, message):
        """Get response about available rooms"""
        # Get all rooms
        total_rooms = Room.objects.count()
        
        # Get booked rooms for today and tomorrow
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        booked_today = Booking.objects.filter(
            check_in__lte=today,
            check_out__gt=today,
            status='CONFIRMED'
        ).values_list('room_id', flat=True)
        
        available_today = total_rooms - len(set(booked_today))
        
        # Group by type
        rooms_by_type = {}
        for room in Room.objects.all():
            room_type = room.get_room_type_display()
            if room_type not in rooms_by_type:
                rooms_by_type[room_type] = 0
            rooms_by_type[room_type] += 1
        
        response = f"**Room Availability** (Today)\n\n"
        response += f"📊 Total Available: {available_today}/{total_rooms} rooms\n\n"
        response += "Available by type:\n"
        
        for room_type in sorted(rooms_by_type.keys()):
            total = rooms_by_type[room_type]
            booked = Booking.objects.filter(
                room__room_type=room_type,
                check_in__lte=today,
                check_out__gt=today,
                status='CONFIRMED'
            ).count()
            available = total - booked
            response += f"• **{room_type}**: {available}/{total} available\n"
        
        response += "\nWant to make a reservation? 📅"
        return response
    
    def get_booking_steps_response(self, message):
        """Get response about booking process"""
        response = """**How to Book with Us** 📚

Here are the simple steps:

1️⃣ **Browse Rooms**
   • Visit our room list
   • Check prices and amenities
   • See recommendations for you

2️⃣ **Select Your Room**
   • Click "Book Now" on your chosen room
   • Pick your check-in and check-out dates
   • Add special requests if needed

3️⃣ **Confirm Booking**
   • Review booking summary
   • See total price breakdown
   • Agree to terms & conditions

4️⃣ **Complete Payment**
   • Your booking is confirmed!
   • Receive confirmation email
   • See booking reference number

That's it! You're all set to enjoy your stay. 🎉

Any questions? Feel free to ask! 😊"""
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
• Cancel up to 7 days before check-in
• Full refund guaranteed
• No questions asked

**Partial Refund:**
• Cancel 3-7 days before check-in: 50% refund
• Cancel 1-3 days before check-in: 25% refund

**Non-Refundable:**
• Cancel within 24 hours of check-in: No refund
• No-show: No refund

**How to Cancel:**
1. Go to "My Bookings" in your account
2. Select the booking you want to cancel
3. Click "Cancel Booking"
4. Confirm cancellation
5. Refund will be processed within 3-5 business days

**Need to Change Dates?**
• You can modify your booking up to 7 days before check-in
• Any price difference will be adjusted

Have questions? Contact us anytime! 📞"""
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
        response = """**What I Can Help With** 🤖

I can answer questions about:

💰 **Pricing**
• Ask: "What are your room prices?"

📅 **Availability**
• Ask: "Do you have available rooms?"

📚 **Booking**
• Ask: "How do I book a room?"

⏰ **Check-in/Check-out**
• Ask: "What's your check-in time?"

🔄 **Cancellations**
• Ask: "What's your cancellation policy?"

🛏️ **Room Details**
• Ask: "Tell me about your rooms"

📍 **Location & Directions**
• Ask: "Where are you located?"

📞 **Contact**
• Ask: "How can I reach you?"

**Pro Tips:**
• Ask me naturally - no special keywords needed
• I'm here 24/7 to help
• For complex issues, I'll connect you with a real agent

What would you like to know? 😊"""
        return response
    
    def get_unknown_response(self, message):
        """Get response for unknown queries"""
        response = """Hmm, I'm not sure about that. 🤔

I can help you with:
• 💰 Room prices
• 📅 Room availability
• 📚 Booking steps
• ⏰ Check-in/check-out times
• 🔄 Cancellation policy
• 🛏️ Room details
• 📍 Location info
• 📞 Contact information

Try asking me something like:
"What are your room prices?"
"How do I book a room?"
"Do you have availability?"

Or type **help** to see all options! 😊"""
        return response
    
    def get_greeting_response(self):
        """Get greeting response"""
        response = """👋 Hello! I'm your **Hotel Assistant**

I'm here to answer questions about:
• Room prices & availability
• Booking process
• Check-in/check-out times
• Cancellation policy
• Room details
• Location & contact info

Type **help** to see all options, or just ask me anything! 😊"""
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
                'response': self.get_help_response(),
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
            'room_details': self.get_room_details_response,
            'contact': self.get_contact_response,
            'location': self.get_location_response,
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
