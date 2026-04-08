"""
Staff URLs - Routes for staff members
"""

from django.urls import path
from . import views_staff

app_name = 'staff'

urlpatterns = [
    # Dashboard
    path('', views_staff.staff_dashboard, name='dashboard'),
    
    # Room Management
    path('rooms/', views_staff.room_status, name='room_status'),
    path('rooms/<int:room_id>/', views_staff.room_detail_staff, name='room_detail'),
    path('rooms/<int:room_id>/mark-clean/', views_staff.mark_room_clean, name='mark_clean'),
    
    # Check-in/Check-out
    path('check-in-checkout/', views_staff.check_in_checkout_list, name='check_in_checkout'),
    
    # Manual Booking (Walk-in)
    path('manual-booking/', views_staff.manual_booking, name='manual_booking'),
    
    # Guest Services
    path('guest-services/', views_staff.guest_services, name='guest_services'),
    
    # Reports
    path('reports/', views_staff.staff_reports, name='reports'),
]
