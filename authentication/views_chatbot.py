"""
Chatbot Views
Handles AJAX requests for chatbot responses
"""

from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.utils.html import escape
from authentication.chatbot_engine import ChatbotEngine
import json


@require_POST
@csrf_exempt  # AJAX from frontend, need to handle CSRF separately or exempt
def get_chatbot_response(request):
    """
    AJAX endpoint for chatbot responses
    Expects POST with 'message' parameter
    Returns JSON response
    """
    try:
        # Get message from request
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            user_message = data.get('message', '').strip()
        else:
            user_message = request.POST.get('message', '').strip()
        
        if not user_message:
            return JsonResponse({
                'success': False,
                'error': 'Message cannot be empty'
            }, status=400)
        
        # Limit message length to prevent abuse
        if len(user_message) > 500:
            user_message = user_message[:500]
        
        # Get response from chatbot
        chatbot = ChatbotEngine()
        result = chatbot.process_message(user_message)
        
        return JsonResponse({
            'success': True,
            'response': result['response'],
            'intent': result['intent'],
            'confidence': result['confidence'],
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON format'
        }, status=400)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'An error occurred: ' + str(e)
        }, status=500)


@require_GET
def chatbot_info(request):
    """
    Get chatbot information and capabilities
    """
    return JsonResponse({
        'success': True,
        'name': 'Hotel Assistant',
        'capabilities': [
            'Room prices',
            'Room availability',
            'Booking steps',
            'Check-in/check-out times',
            'Cancellation policy',
            'Room details',
            'Location information',
            'Contact information',
        ],
        'available_24_7': True,
    })
