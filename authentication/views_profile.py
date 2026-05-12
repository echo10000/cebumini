from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .forms import (
    AdminProfileForm,
    ChangePasswordForm,
    ManagerProfileForm,
    StaffProfileForm,
    UpdateEmailForm,
    UserProfileForm,
)
from .models import AdminProfile, ManagerProfile, StaffProfile, UserProfile, UserRole


def _employee_id_for_user(user):
    return f'EMP-{user.id:05d}'


def _role_flags(user):
    return {
        'is_staff_role': user.role in {UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN},
        'is_manager_role': user.role in {UserRole.MANAGER, UserRole.ADMIN},
        'is_admin_role': user.role == UserRole.ADMIN,
    }


def _base_template_for_user(user):
    if user.role == UserRole.ADMIN:
        return 'admin/admin_base.html'
    if user.role == UserRole.MANAGER:
        return 'manager/manager_base.html'
    if user.role == UserRole.STAFF:
        return 'staff/staff_base.html'
    return 'guest/guest_base.html'


def _get_profile_context(user):
    flags = _role_flags(user)
    profile, _ = UserProfile.objects.get_or_create(user=user)
    staff_profile = None
    manager_profile = None
    admin_profile = None

    if flags['is_staff_role']:
        staff_profile, _ = StaffProfile.objects.get_or_create(
            user=user,
            defaults={'employee_id': _employee_id_for_user(user)}
        )

    if flags['is_manager_role']:
        manager_profile, _ = ManagerProfile.objects.get_or_create(user=user)

    if flags['is_admin_role']:
        admin_profile, _ = AdminProfile.objects.get_or_create(user=user)

    return {
        'base_template': _base_template_for_user(user),
        'profile': profile,
        'staff_profile': staff_profile,
        'manager_profile': manager_profile,
        'admin_profile': admin_profile,
        **flags,
    }


@login_required(login_url='auth:login')
@require_http_methods(['GET'])
def profile_view(request):
    context = _get_profile_context(request.user)
    return render(request, 'profile.html', context)


@login_required(login_url='auth:login')
@require_http_methods(['GET', 'POST'])
def profile_edit_view(request):
    context = _get_profile_context(request.user)
    profile = context['profile']
    staff_profile = context['staff_profile']
    manager_profile = context['manager_profile']
    admin_profile = context['admin_profile']

    if request.method == 'POST':
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        staff_form = StaffProfileForm(request.POST, instance=staff_profile) if context['is_staff_role'] else None
        manager_form = ManagerProfileForm(request.POST, instance=manager_profile) if context['is_manager_role'] else None
        admin_form = AdminProfileForm(request.POST, instance=admin_profile) if context['is_admin_role'] else None

        forms = [profile_form]
        if staff_form:
            forms.append(staff_form)
        if manager_form:
            forms.append(manager_form)
        if admin_form:
            forms.append(admin_form)

        if all(form.is_valid() for form in forms):
            profile_form.save()
            if staff_form:
                staff_form.save()
            if manager_form:
                manager_form.save()
            if admin_form:
                admin_form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('profile')

        messages.error(request, 'Please correct the errors below.')
    else:
        profile_form = UserProfileForm(instance=profile)
        staff_form = StaffProfileForm(instance=staff_profile) if context['is_staff_role'] else None
        manager_form = ManagerProfileForm(instance=manager_profile) if context['is_manager_role'] else None
        admin_form = AdminProfileForm(instance=admin_profile) if context['is_admin_role'] else None

    context.update({
        'profile_form': profile_form,
        'staff_form': staff_form,
        'manager_form': manager_form,
        'admin_form': admin_form,
    })
    return render(request, 'profile_edit.html', context)


@login_required(login_url='auth:login')
@require_http_methods(['GET', 'POST'])
def change_password_view(request):
    if request.method == 'POST':
        form = ChangePasswordForm(request.user, request.POST)
        if form.is_valid():
            request.user.set_password(form.cleaned_data['new_password'])
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Your password has been changed successfully.')
            return redirect('profile')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = ChangePasswordForm(request.user)

    return render(request, 'change_password.html', {
        'base_template': _base_template_for_user(request.user),
        'form': form,
    })


@login_required(login_url='auth:login')
@require_http_methods(['GET', 'POST'])
def change_email_view(request):
    if request.method == 'POST':
        form = UpdateEmailForm(request.user, request.POST)
        if form.is_valid():
            request.user.email = form.cleaned_data['new_email']
            request.user.save(update_fields=['email', 'updated_at'])
            messages.success(request, 'Your email address has been updated successfully.')
            return redirect('profile')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = UpdateEmailForm(request.user)

    return render(request, 'change_email.html', {
        'base_template': _base_template_for_user(request.user),
        'form': form,
    })
