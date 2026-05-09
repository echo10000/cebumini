from django.urls import path
from .views_bookings import (
    create_booking_view,
    confirm_booking_view,
    booking_detail_view,
    booking_history_view,
    cancel_booking_view,
    admin_bookings_view,
    admin_cancel_booking_view,
    admin_confirm_booking_view,
    guest_submit_complaint_view,
    guest_my_complaints_view,
    guest_complaint_detail_view,
    guest_request_refund_view,
    guest_my_refund_requests_view,
    guest_refund_detail_view,
)
from .views_payments import (
    payment_success_view,
    payment_failed_view,
    payment_pending_view,
)
from .views_paymongo import (
    paymongo_payment_view,
    paymongo_callback,
    paymongo_webhook,
)

app_name = 'bookings'

urlpatterns = [
    # Guest booking URLs
    path('<int:room_id>/create/', create_booking_view, name='create_booking'),
    path('confirm/', confirm_booking_view, name='confirm_booking'),
    path('<int:booking_id>/', booking_detail_view, name='booking_detail'),
    path('history/', booking_history_view, name='booking_history'),
    path('<int:booking_id>/cancel/', cancel_booking_view, name='cancel_booking'),
    
    # PayMongo Payment URLs (ONLY payment method)
    path('<int:booking_id>/payment/', paymongo_payment_view, name='paymongo_payment'),
    path('<int:booking_id>/payment/success/', payment_success_view, name='payment_success'),
    path('<int:booking_id>/payment/failed/', payment_failed_view, name='payment_failed'),
    path('<int:booking_id>/payment/pending/', payment_pending_view, name='payment_pending'),
    path('paymongo-callback/', paymongo_callback, name='paymongo_callback'),
    path('webhook/paymongo/', paymongo_webhook, name='paymongo_webhook'),
    
    # Admin booking URLs
    path('admin/all/', admin_bookings_view, name='admin_bookings'),
    path('admin/<int:booking_id>/confirm/', admin_confirm_booking_view, name='admin_confirm_booking'),
    path('admin/<int:booking_id>/cancel/', admin_cancel_booking_view, name='admin_cancel_booking'),
    
    # Guest complaint URLs
    path('<int:booking_id>/complaint/submit/', guest_submit_complaint_view, name='submit_complaint'),
    path('complaints/', guest_my_complaints_view, name='my_complaints'),
    path('complaints/<int:complaint_id>/', guest_complaint_detail_view, name='complaint_detail'),
    
    # Guest refund URLs
    path('<int:booking_id>/refund/request/', guest_request_refund_view, name='request_refund'),
    path('refunds/', guest_my_refund_requests_view, name='my_refunds'),
    path('refunds/<int:refund_id>/', guest_refund_detail_view, name='refund_detail'),
]
