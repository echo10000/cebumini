from django.urls import path
from . import views

app_name = 'auth'

urlpatterns = [
    path('terms/', views.terms_view, name='terms'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('accept-terms/', views.accept_terms_view, name='accept_terms'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('contact/', views.contact_view, name='contact'),
    path('2fa/setup/', views.setup_2fa, name='setup_2fa'),
    path('2fa/backup-codes/', views.view_backup_codes, name='2fa_backup_codes'),
    path('2fa/verify/', views.verify_2fa_login, name='verify_2fa_login'),
    path('2fa/disable/', views.disable_2fa, name='disable_2fa'),
]
