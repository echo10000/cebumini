from django.urls import path
from . import views_admin
from .views_paymongo import refund_paymongo_payment

app_name = 'admin_panel'

urlpatterns = [
    # Dashboard
    path('', views_admin.admin_dashboard, name='dashboard'),
    
    # Payment Management
    path('payments/', views_admin.payment_management, name='payment_management'),
    path('payments/<int:payment_id>/', views_admin.payment_detail, name='payment_detail'),
    path('payments/<int:payment_id>/approve/', views_admin.approve_payment, name='approve_payment'),
    path('payments/<int:payment_id>/reject/', views_admin.reject_payment, name='reject_payment'),
    
    # Room Management
    path('rooms/', views_admin.room_management, name='room_management'),
    path('rooms/<int:room_id>/', views_admin.room_detail_admin, name='room_detail_admin'),
    path('rooms/<int:room_id>/delete/', views_admin.room_delete_admin, name='room_delete'),
    
    # Booking Management
    path('bookings/', views_admin.booking_management, name='booking_management'),
    path('bookings/<int:booking_id>/', views_admin.booking_detail, name='booking_detail'),
    path('bookings/<int:booking_id>/edit/', views_admin.booking_edit, name='booking_edit'),
    path('bookings/refund/', refund_paymongo_payment, name='refund_paymongo_payment'),
    
    # User Management
    path('users/', views_admin.user_management, name='user_management'),

    # Testimonials
    path('testimonials/<int:testimonial_id>/approve/', views_admin.approve_testimonial, name='approve_testimonial'),
    path('testimonials/<int:testimonial_id>/reject/', views_admin.reject_testimonial, name='reject_testimonial'),
    
    # Reports
    path('reports/', views_admin.admin_reports, name='reports'),
    path('reports/export/bookings/', views_admin.export_bookings_csv, name='export_bookings_csv'),
    path('reports/export/payments/', views_admin.export_payments_csv, name='export_payments_csv'),
    path('reports/export/guests/', views_admin.export_guests_csv, name='export_guests_csv'),
]
