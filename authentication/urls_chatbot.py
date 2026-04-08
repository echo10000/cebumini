"""
Chatbot URLs
"""

from django.urls import path
from .views_chatbot import get_chatbot_response, chatbot_info

urlpatterns = [
    path('api/response/', get_chatbot_response, name='chatbot_response'),
    path('api/info/', chatbot_info, name='chatbot_info'),
]
