from django.urls import path

from . import views_profile


urlpatterns = [
    path('profile/', views_profile.profile_view, name='profile'),
    path('profile/edit/', views_profile.profile_edit_view, name='profile_edit'),
    path('profile/change-password/', views_profile.change_password_view, name='change_password'),
    path('profile/change-email/', views_profile.change_email_view, name='change_email'),
]
