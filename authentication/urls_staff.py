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
    path('check-in/<int:booking_id>/', views_staff.check_in_booking, name='check_in_booking'),
    
    # Manual Booking (Walk-in)
    path('manual-booking/', views_staff.manual_booking, name='manual_booking'),
    path('pending-balance/', views_staff.pending_balance_bookings, name='pending_balance'),
    path('process-payment/<int:booking_id>/', views_staff.process_remaining_payment, name='process_remaining_payment'),
    
    # Guest Services
    path('guest-services/', views_staff.guest_services, name='guest_services'),
    path('messages/<int:message_id>/detail/', views_staff.staff_message_detail_view, name='message_detail'),
    path('messages/<int:message_id>/', views_staff.get_message_details, name='message_details'),
    path('messages/<int:message_id>/reply/', views_staff.send_reply, name='send_reply'),
    
    # Reports
    path('reports/', views_staff.staff_reports, name='reports'),
    
    # Escalated Complaints
    path('complaints/', views_staff.staff_escalated_complaints_view, name='escalated_complaints'),
    path('complaints/<int:complaint_id>/', views_staff.staff_complaint_detail_view, name='complaint_detail'),
    
    # Requested Refunds
    path('refunds/', views_staff.staff_requested_refunds_view, name='requested_refunds'),
    path('refunds/<int:refund_id>/', views_staff.staff_refund_detail_view, name='refund_detail'),
]
