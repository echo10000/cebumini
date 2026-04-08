from django.urls import path
from . import views_recommendations

app_name = 'recommendations'

urlpatterns = [
    # Recommendations endpoints
    path('api/recommendations/', views_recommendations.get_user_recommendations, name='api_recommendations'),
    path('profile/', views_recommendations.user_booking_profile, name='user_profile'),
    path('all/', views_recommendations.room_recommendations_page, name='recommendations'),
]
