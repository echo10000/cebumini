"""
Chatbot Views - Enhanced with Gemini API Support
Handles AJAX requests for chatbot responses with fallback to keyword system
"""

from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.utils.html import escape
from datetime import datetime
from authentication.chatbot_engine import ChatbotEngine
import json
import logging

logger = logging.getLogger(__name__)


def get_current_availability():
    """Get current room availability from database"""
    try:
        from authentication.models import Room, Booking
        from datetime import datetime, timedelta
        
        today = datetime.now().date()
        
        total_rooms = Room.objects.count()
        booked_today = Booking.objects.filter(
            check_in__lte=today,
            check_out__gt=today,
            status='CONFIRMED'
        ).values_list('room_id', flat=True).distinct()
        
        available_rooms = total_rooms - len(booked_today)
        
        # Get availability by room type
        availability_by_type = {}
        for room in Room.objects.all():
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


@require_POST
@csrf_exempt  # AJAX from frontend, need to handle CSRF separately or exempt
def get_chatbot_response(request):
    """
    AJAX endpoint for chatbot responses
    Supports both Gemini AI and keyword-based fallback
    
    Expects POST with:
        - 'message': User's message (required)
        - 'use_ai': Whether to use Gemini (optional, default: true)
    
    Returns JSON response
    """
    try:
        # Get message from request
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            user_message = data.get('message', '').strip()
            use_ai = data.get('use_ai', True)  # Default to AI
        else:
            user_message = request.POST.get('message', '').strip()
            use_ai = request.POST.get('use_ai', 'true').lower() == 'true'
        
        if not user_message:
            return JsonResponse({
                'success': False,
                'error': 'Message cannot be empty',
                'response': 'Please ask me something! 😊'
            }, status=400)
        
        # Limit message length to prevent abuse
        if len(user_message) > 500:
            user_message = user_message[:500]
        
        # Try Gemini first if enabled
        if use_ai:
            try:
                from authentication.gemini_chatbot import ask_gemini
                
                availability = get_current_availability()
                response_text = ask_gemini(user_message, availability)
                
                return JsonResponse({
                    'success': True,
                    'response': response_text,
                    'use_ai': True,
                    'status': 'gemini_success'
                })
            
            except Exception as e:
                logger.warning(f"Gemini failed, falling back to keyword system: {e}")
                # Fall through to keyword system below
        
        # Fallback: Use keyword-based system
        chatbot = ChatbotEngine()
        result = chatbot.process_message(user_message)
        
        return JsonResponse({
            'success': True,
            'response': result['response'],
            'intent': result['intent'],
            'confidence': result['confidence'],
            'use_ai': False,
            'status': 'keyword_fallback' if use_ai else 'keyword_primary'
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON format',
            'response': 'Please send valid JSON'
        }, status=400)
    
    except Exception as e:
        logger.error(f"Chatbot error: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}',
            'response': 'Sorry, something went wrong. Let me connect you with our staff. Call +63 32 412 3456'
        }, status=500)


@require_GET
def chatbot_info(request):
    """
    Get chatbot information and capabilities
    """
    return JsonResponse({
        'success': True,
        'name': 'Echo - Hotel Assistant',
        'capabilities': [
            'Room prices',
            'Room availability',
            'Booking steps',
            'Check-in/check-out times',
            'Cancellation policy',
            'Room details',
            'Location information',
            'Contact information',
            'Room recommendations',
            'Pet policies',
            'Amenities information'
        ],
        'ai_powered': True,
        'available_24_7': True,
    })


@require_GET
def chatbot_availability(request):
    """
    Get current room availability endpoint
    
    Returns:
        {
            "success": true,
            "total_rooms": 50,
            "available_count": 35,
            "by_type": {...},
            "check_date": "2024-04-16"
        }
    """
    try:
        availability = get_current_availability()
        return JsonResponse({
            'success': True,
            **availability
        })
    except Exception as e:
        logger.error(f"Error getting availability: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_POST
@csrf_exempt
def chatbot_view(request):
    """
    Main chatbot API endpoint for /api/chat/
    
    Accepts POST requests with JSON body containing "message"
    Queries Room model for available rooms
    Calls ask_gemini() with user message and availability data
    Returns JSON: {"reply": "..."}
    
    Usage:
        POST /api/chat/
        {
            "message": "What are your room prices?"
        }
    
    Response:
        {
            "reply": "Echo's response here..."
        }
    """
    try:
        # Parse JSON body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {'error': 'Invalid JSON'}, 
                status=400
            )
        
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return JsonResponse(
                {'error': 'Message is required'},
                status=400
            )
        
        # Query available rooms from database
        from authentication.models import Room
        
        available_rooms = Room.objects.filter(is_available=True)
        
        if not available_rooms.exists():
            # If no rooms in DB, use default availability
            availability_data = {
                'total_rooms': 0,
                'available_count': 0,
                'by_type': {},
                'check_date': datetime.now().date().strftime('%Y-%m-%d')
            }
        else:
            # Build availability data from database
            room_types = {}
            for room in available_rooms:
                room_type = room.get_room_type_display()
                
                if room_type not in room_types:
                    room_types[room_type] = {
                        'price': float(room.price_per_night),
                        'count': 0
                    }
                room_types[room_type]['count'] += 1
            
            # Format as readable string for Gemini
            availability_text = f"Available rooms today: {available_rooms.count()} rooms\n\n"
            for room_type, info in room_types.items():
                availability_text += f"• {room_type}: {info['count']} room(s) @ ₱{info['price']:,.2f}/night\n"
            
            availability_data = {
                'total_rooms': Room.objects.count(),
                'available_count': available_rooms.count(),
                'by_type': room_types,
                'check_date': datetime.now().date().strftime('%Y-%m-%d')
            }
        
        # Call ask_gemini with user message and availability data
        from authentication.gemini_chatbot import ask_gemini
        
        response = ask_gemini(user_message, availability_data)
        
        return JsonResponse({'reply': response})
    
    except Exception as e:
        logger.error(f"Chatbot view error: {e}", exc_info=True)
        return JsonResponse(
            {'error': f'Server error: {str(e)}'},
            status=500
        )
