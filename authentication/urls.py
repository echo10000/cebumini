from django.urls import path
from . import views, views_manager, views_staff, views_bookings

app_name = 'auth'

urlpatterns = [
    # ============= AUTHENTICATION ROUTES =============
    path('terms/', views.terms_view, name='terms'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('accept-terms/', views.accept_terms_view, name='accept_terms'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('contact/', views.contact_view, name='contact'),
    
    # ============= 2FA ROUTES =============
    path('2fa/setup/', views.setup_2fa, name='setup_2fa'),
    path('2fa/backup-codes/', views.view_backup_codes, name='2fa_backup_codes'),
    path('2fa/verify/', views.verify_2fa_login, name='verify_2fa_login'),
    path('2fa/disable/', views.disable_2fa, name='disable_2fa'),
    
    # ============= MANAGER ROUTES =============
    path('manager/dashboard/', views_manager.manager_dashboard_view, name='manager_dashboard'),
    path('manager/refunds/', views_manager.manager_refund_requests_view, name='manager_refunds'),
    path('manager/refunds/<int:refund_request_id>/approve/', views_manager.approve_refund_request_view, name='manager_approve_refund'),
    path('manager/complaints/', views_manager.complaints_escalations_view, name='manager_complaints'),
    path('manager/complaints/<int:escalation_id>/resolve/', views_manager.resolve_complaint_escalation_view, name='manager_resolve_complaint'),
    path('manager/staff/', views_manager.staff_members_view, name='manager_staff'),
    path('manager/staff/register/', views_manager.register_staff_view, name='manager_register_staff'),
    path('manager/staff/<int:staff_id>/deactivate/', views_manager.deactivate_staff_view, name='manager_deactivate_staff'),
    path('manager/staff/<int:staff_id>/dashboard/', views_manager.staff_dashboard_view, name='manager_staff_dashboard'),
    
    # ============= STAFF ENHANCEMENTS =============
    path('staff/room/<int:room_id>/status/', views_staff.update_room_housekeeping_status, name='staff_update_room_status'),
    path('staff/booking/<int:booking_id>/escalate/', views_staff.escalate_guest_complaint, name='staff_escalate_complaint'),
    path('staff/booking/<int:booking_id>/request-refund/', views_staff.request_refund, name='staff_request_refund'),
    
    # ============= GUEST ENHANCEMENTS =============
    path('bookings/<int:booking_id>/invoice/', views_bookings.download_invoice_view, name='download_invoice'),
]
