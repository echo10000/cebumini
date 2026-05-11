import smtplib

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Send a real test email using the active Django email backend.'

    def add_arguments(self, parser):
        parser.add_argument('--to', default=None, help='Recipient email address.')

    def handle(self, *args, **options):
        recipient = options['to'] or settings.EMAIL_HOST_USER
        if not recipient:
            raise CommandError('No recipient provided. Use --to or set EMAIL_HOST_USER.')

        self.stdout.write(f'EMAIL_BACKEND={settings.EMAIL_BACKEND}')
        self.stdout.write(f'EMAIL_HOST={settings.EMAIL_HOST}:{settings.EMAIL_PORT}')
        self.stdout.write(f'EMAIL_HOST_USER={settings.EMAIL_HOST_USER or "(blank)"}')
        self.stdout.write(f'EMAIL_HOST_PASSWORD_SET={bool(settings.EMAIL_HOST_PASSWORD)}')
        self.stdout.write(f'DEFAULT_FROM_EMAIL={settings.DEFAULT_FROM_EMAIL}')
        self.stdout.write(f'RECIPIENT={recipient}')

        if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
            raise CommandError(
                'Email is using the console backend, so nothing will reach Gmail. '
                'Set EMAIL_HOST_PASSWORD to a valid Google App Password, then restart Django.'
            )

        try:
            sent = send_mail(
                subject='Cebu Hotel test email',
                message='This is a test email from your Django app.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
        except smtplib.SMTPAuthenticationError as exc:
            raise CommandError(
                'Gmail rejected the username or app password. Generate a new Google App Password, '
                'paste it into EMAIL_HOST_PASSWORD, then restart Django.'
            ) from exc
        except smtplib.SMTPResponseException as exc:
            message = exc.smtp_error.decode(errors='replace') if isinstance(exc.smtp_error, bytes) else str(exc.smtp_error)
            if exc.smtp_code == 550 and 'sending limit' in message.lower():
                raise CommandError(
                    'Gmail accepted the password but refused to send because the account daily sending limit is exceeded. '
                    'Wait for Gmail quota to reset or use another SMTP account/provider.'
                ) from exc
            raise CommandError(f'Email send failed: {exc.smtp_code} {message}') from exc
        except Exception as exc:
            raise CommandError(f'Email send failed: {exc}') from exc

        if sent != 1:
            raise CommandError(f'Email backend returned {sent}; expected 1.')

        self.stdout.write(self.style.SUCCESS('Test email sent successfully.'))
