"""
URL configuration for cebuhotel project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView
from authentication.views import home_view, allauth_login_redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Redirect allauth login to our custom login
    path('accounts/login/', allauth_login_redirect, name='allauth_login_redirect'),
    path('accounts/', include('allauth.urls')),  # Social auth URLs (allauth backend only)
    
    path('auth/', include('authentication.urls')),  # PRIMARY login: /auth/login/
    path('rooms/', include('authentication.urls_rooms')),
    path('bookings/', include('authentication.urls_bookings')),
    path('dashboard/', include('authentication.urls_dashboard')),
    path('recommendations/', include('authentication.urls_recommendations')),
    path('chatbot/', include('authentication.urls_chatbot')),
    path('admin-panel/', include('authentication.urls_admin')),
    path('staff/', include('authentication.urls_staff')),
    path('', home_view, name='home'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
