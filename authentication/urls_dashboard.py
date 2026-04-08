from django.urls import path
from . import views_dashboard

app_name = 'dashboard'

urlpatterns = [
    # Dashboard Views
    path('', views_dashboard.dashboard_view, name='admin_dashboard'),
    path('revenue/', views_dashboard.revenue_analytics_view, name='revenue_analytics'),
    path('occupancy/', views_dashboard.occupancy_analytics_view, name='occupancy_analytics'),
    path('bookings/', views_dashboard.booking_analytics_view, name='booking_analytics'),
]
