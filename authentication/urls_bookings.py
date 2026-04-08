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
)
from .views_payments import (
    payment_page_view,
    stripe_payment_view,
    gcash_payment_view,
    bank_transfer_payment_view,
    payment_success_view,
    payment_failed_view,
    payment_pending_view,
    stripe_webhook_view,
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
    
    # Payment URLs
    path('<int:booking_id>/payment/', payment_page_view, name='payment_page'),
    path('<int:booking_id>/payment/stripe/', stripe_payment_view, name='stripe_payment'),
    path('<int:booking_id>/payment/paymongo/', paymongo_payment_view, name='paymongo_payment'),
    path('<int:booking_id>/payment/gcash/', gcash_payment_view, name='gcash_payment'),
    path('<int:booking_id>/payment/bank-transfer/', bank_transfer_payment_view, name='bank_transfer_payment'),
    path('<int:booking_id>/payment/success/', payment_success_view, name='payment_success'),
    path('<int:booking_id>/payment/failed/', payment_failed_view, name='payment_failed'),
    path('<int:booking_id>/payment/pending/', payment_pending_view, name='payment_pending'),
    path('paymongo-callback/', paymongo_callback, name='paymongo_callback'),
    path('webhook/stripe/', stripe_webhook_view, name='stripe_webhook'),
    path('webhook/paymongo/', paymongo_webhook, name='paymongo_webhook'),
    
    # Admin booking URLs
    path('admin/all/', admin_bookings_view, name='admin_bookings'),
    path('admin/<int:booking_id>/confirm/', admin_confirm_booking_view, name='admin_confirm_booking'),
    path('admin/<int:booking_id>/cancel/', admin_cancel_booking_view, name='admin_cancel_booking'),
]
