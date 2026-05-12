from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import EmailOTP


User = get_user_model()


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class RegistrationEmailOTPTests(TestCase):
    def test_new_guest_must_verify_email_with_otp(self):
        response = self.client.post(reverse('auth:register'), {
            'email': 'newguest@example.com',
            'first_name': 'New',
            'last_name': 'Guest',
            'phone': '09123456789',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'agree_to_terms': 'on',
        })

        self.assertRedirects(
            response,
            reverse('auth:verify_otp'),
            fetch_redirect_response=False,
        )

        user = User.objects.get(email='newguest@example.com')
        self.assertFalse(user.is_email_verified)
        self.assertEqual(self.client.session['email_otp_user_id'], user.id)
        self.assertEqual(self.client.session['email_otp_purpose'], 'registration')
        self.assertEqual(len(mail.outbox), 1)

        otp = EmailOTP.objects.get(user=user, is_used=False)
        response = self.client.post(reverse('auth:verify_otp'), {
            'otp_code': otp.otp_code,
        })

        self.assertRedirects(
            response,
            reverse('auth:otp_success'),
            fetch_redirect_response=False,
        )
        user.refresh_from_db()
        otp.refresh_from_db()
        self.assertTrue(user.is_email_verified)
        self.assertTrue(otp.is_used)

    def test_unverified_guest_login_resends_otp_instead_of_logging_in(self):
        user = User.objects.create_user(
            username='pending',
            email='pending@example.com',
            password='StrongPass123!',
            first_name='Pending',
            last_name='Guest',
            role='GUEST',
            is_email_verified=False,
            terms_accepted=True,
        )

        response = self.client.post(reverse('auth:login'), {
            'username': 'pending@example.com',
            'password': 'StrongPass123!',
        })

        self.assertRedirects(
            response,
            reverse('auth:verify_otp'),
            fetch_redirect_response=False,
        )
        self.assertEqual(self.client.session['email_otp_user_id'], user.id)
        self.assertEqual(self.client.session['email_otp_purpose'], 'registration')
        self.assertEqual(len(mail.outbox), 1)
