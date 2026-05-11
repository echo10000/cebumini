"""
Access Control & Permission Decorators
Handles login requirements and role-based access control
"""

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from functools import wraps

from .utils import get_two_fa_status, is_two_fa_configured, user_requires_2fa


def _redirect_if_2fa_required(request):
    if user_requires_2fa(request.user) and not is_two_fa_configured(request.user):
        from django.contrib import messages
        messages.warning(request, 'Two-factor authentication is required for admin and manager accounts.')
        return redirect(reverse('auth:setup_2fa'))

    two_fa = get_two_fa_status(request.user)
    if two_fa and request.session.get('2fa_verified_user_id') != request.user.id:
        if two_fa.method == 'EMAIL':
            from .otp_utils import send_otp_email
            send_otp_email(request.user)
            request.session['email_otp_user_id'] = request.user.id
            request.session['email_otp_remember_me'] = False
            return redirect(reverse('auth:verify_otp'))
        request.session['2fa_user_id'] = request.user.id
        request.session['2fa_remember_me'] = False
        return redirect(reverse('auth:verify_2fa_login'))
    return None


class Require2FAMixin:
    """Require completed 2FA setup for admin and manager class-based views."""

    def dispatch(self, request, *args, **kwargs):
        response = _redirect_if_2fa_required(request)
        if response:
            return response
        return super().dispatch(request, *args, **kwargs)


def admin_required(view_func):
    """
    Decorator to restrict access to admin users only
    Redirects non-admins to home page with error message
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(reverse('login'))
        
        if not request.user.is_admin():
            from django.contrib import messages
            messages.error(request, 'You do not have permission to access this page.')
            return redirect(reverse('home'))

        two_fa_response = _redirect_if_2fa_required(request)
        if two_fa_response:
            return two_fa_response
        
        return view_func(request, *args, **kwargs)
    return wrapper


def guest_required(view_func):
    """
    Decorator to restrict access to authenticated guests (non-admins)
    Redirects admins to admin dashboard
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(reverse('login'))
        
        if request.user.is_admin():
            return redirect(reverse('admin_dashboard'))
        
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_or_owner_required(view_func):
    """
    Decorator for resources that admins or owners can access
    e.g., Admins can see all bookings, guests see only their own
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(reverse('login'))
        
        # Admins can access everything
        if request.user.is_admin():
            return view_func(request, *args, **kwargs)
        
        # Non-admins continue to view
        return view_func(request, *args, **kwargs)
    return wrapper


def ajax_login_required(view_func):
    """
    Decorator for AJAX endpoints that require login
    Returns JSON error instead of redirect
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'Authentication required',
                'redirect': reverse('login')
            }, status=401)
        
        return view_func(request, *args, **kwargs)
    return wrapper


def ajax_admin_required(view_func):
    """
    Decorator for AJAX endpoints that require admin access
    Returns JSON error instead of redirect
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'Authentication required',
                'redirect': reverse('login')
            }, status=401)
        
        if not request.user.is_admin():
            return JsonResponse({
                'success': False,
                'error': 'Admin access required'
            }, status=403)
        
        return view_func(request, *args, **kwargs)
    return wrapper


def ajax_manager_required(view_func):
    """
    Decorator for AJAX endpoints that require manager access
    Returns JSON error instead of redirect
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'Authentication required',
                'redirect': reverse('login')
            }, status=401)
        
        if not request.user.is_manager():
            return JsonResponse({
                'success': False,
                'error': 'Manager access required'
            }, status=403)
        
        return view_func(request, *args, **kwargs)
    return wrapper


def ajax_manager_or_admin_required(view_func):
    """
    Decorator for AJAX endpoints that require manager or admin access
    Returns JSON error instead of redirect
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'Authentication required',
                'redirect': reverse('login')
            }, status=401)
        
        if not (request.user.is_manager() or request.user.is_admin()):
            return JsonResponse({
                'success': False,
                'error': 'Manager or Admin access required'
            }, status=403)
        
        return view_func(request, *args, **kwargs)
    return wrapper


def staff_required(view_func):
    """
    Decorator to restrict access to staff users only
    Also checks that terms and conditions are accepted
    Redirects non-staff to home page with error message
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(reverse('login'))
        
        if not request.user.is_staff_member():
            from django.contrib import messages
            messages.error(request, 'You do not have permission to access this page.')
            return redirect(reverse('home'))
        
        # Check if staff member has accepted T&C
        if not request.user.has_accepted_terms():
            return redirect(reverse('auth:accept_terms'))
        
        return view_func(request, *args, **kwargs)
    return wrapper


def manager_required(view_func):
    """
    Decorator to restrict access to manager users only
    Also checks that terms and conditions are accepted
    Redirects non-managers to home page with error message
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(reverse('login'))
        
        if not request.user.is_manager():
            from django.contrib import messages
            messages.error(request, 'You do not have permission to access this page.')
            return redirect(reverse('home'))
        
        # Check if manager has accepted T&C
        if not request.user.has_accepted_terms():
            return redirect(reverse('auth:accept_terms'))

        two_fa_response = _redirect_if_2fa_required(request)
        if two_fa_response:
            return two_fa_response
        
        return view_func(request, *args, **kwargs)
    return wrapper


def staff_or_admin_required(view_func):
    """
    Decorator to restrict access to staff and admin users
    Also checks that terms and conditions are accepted
    Redirects non-staff/non-admin to home page with error message
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(reverse('login'))
        
        if not (request.user.is_staff_member() or request.user.is_admin()):
            from django.contrib import messages
            messages.error(request, 'You do not have permission to access this page.')
            return redirect(reverse('home'))
        
        # Check if staff/admin has accepted T&C
        if not request.user.has_accepted_terms():
            return redirect(reverse('auth:accept_terms'))
        
        return view_func(request, *args, **kwargs)
    return wrapper


def manager_or_admin_required(view_func):
    """
    Decorator to restrict access to manager and admin users
    Also checks that terms and conditions are accepted
    Redirects non-manager/non-admin to home page with error message
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(reverse('login'))
        
        if not (request.user.is_manager() or request.user.is_admin()):
            from django.contrib import messages
            messages.error(request, 'You do not have permission to access this page.')
            return redirect(reverse('home'))
        
        # Check if manager/admin has accepted T&C
        if not request.user.has_accepted_terms():
            return redirect(reverse('auth:accept_terms'))

        two_fa_response = _redirect_if_2fa_required(request)
        if two_fa_response:
            return two_fa_response
        
        return view_func(request, *args, **kwargs)
    return wrapper


def staff_manager_or_admin_required(view_func):
    """
    Decorator to restrict access to staff, manager, and admin users
    Also checks that terms and conditions are accepted
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(reverse('login'))
        
        if not (request.user.is_staff_member() or request.user.is_manager() or request.user.is_admin()):
            from django.contrib import messages
            messages.error(request, 'You do not have permission to access this page.')
            return redirect(reverse('home'))
        
        # Check if staff/manager/admin has accepted T&C
        if not request.user.has_accepted_terms():
            return redirect(reverse('auth:accept_terms'))

        two_fa_response = _redirect_if_2fa_required(request)
        if two_fa_response:
            return two_fa_response
        
        return view_func(request, *args, **kwargs)
    return wrapper


def permission_required(permission):
    """
    Generic permission decorator (expandable for future use)
    Supports: 'admin', 'manager', 'staff', 'manager_or_admin', 'staff_or_admin', 'staff_manager_or_admin'
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(reverse('login'))
            
            # Check permission based on type
            has_permission = False
            
            if permission == 'admin':
                has_permission = request.user.is_admin()
            elif permission == 'manager':
                has_permission = request.user.is_manager()
            elif permission == 'staff':
                has_permission = request.user.is_staff_member()
            elif permission == 'manager_or_admin':
                has_permission = request.user.is_manager() or request.user.is_admin()
            elif permission == 'staff_or_admin':
                has_permission = request.user.is_staff_member() or request.user.is_admin()
            elif permission == 'staff_manager_or_admin':
                has_permission = request.user.is_staff_member() or request.user.is_manager() or request.user.is_admin()
            
            if not has_permission:
                from django.contrib import messages
                messages.error(request, 'You do not have permission to perform this action.')
                return redirect(reverse('home'))
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
