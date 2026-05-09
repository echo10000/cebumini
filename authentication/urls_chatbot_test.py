"""
Chatbot URLs
Add these to your main urls.py or include them
"""

from django.urls import path
from django.views.generic import TemplateView
from . import views_chatbot

urlpatterns = [
    # Main chatbot endpoint (POST /api/chat/)
    path('api/chat/', views_chatbot.chatbot_view, name='chatbot_view'),
    
    # Alternative chatbot endpoint (POST /api/chatbot/)
    path('api/chatbot/', views_chatbot.get_chatbot_response, name='chatbot_response'),
    
    # Informational endpoints
    path('api/chatbot/info/', views_chatbot.chatbot_info, name='chatbot_info'),
    path('api/chatbot/availability/', views_chatbot.chatbot_availability, name='chatbot_availability'),
    
    # Test UI
    path('chatbot/test/', TemplateView.as_view(template_name='chatbot_test.html'), name='chatbot_test_ui'),
]
