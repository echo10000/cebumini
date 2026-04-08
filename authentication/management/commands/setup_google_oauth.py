"""
Management command to set up Google OAuth
Usage: python manage.py setup_google_oauth --client-id <ID> --secret <SECRET>
"""

from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp


class Command(BaseCommand):
    help = 'Set up Google OAuth for the application'

    def add_arguments(self, parser):
        parser.add_argument(
            '--client-id',
            type=str,
            help='Google OAuth Client ID',
        )
        parser.add_argument(
            '--secret',
            type=str,
            help='Google OAuth Client Secret',
        )
        parser.add_argument(
            '--domain',
            type=str,
            default='localhost:8000',
            help='Domain for the site (default: localhost:8000)',
        )

    def handle(self, *args, **options):
        client_id = options.get('client_id')
        secret = options.get('secret')
        domain = options.get('domain')

        # If credentials not provided, prompt for them
        if not client_id:
            client_id = input('Enter Google OAuth Client ID: ').strip()
        
        if not secret:
            secret = input('Enter Google OAuth Client Secret: ').strip()

        if not client_id or not secret:
            self.stdout.write(
                self.style.ERROR('Client ID and Secret are required!')
            )
            return

        try:
            # Get or create the site
            site, created = Site.objects.get_or_create(
                domain=domain,
                defaults={'name': 'Cebu Hotel'}
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created site: {domain}')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'Using existing site: {domain}')
                )

            # Get or create the Google OAuth app
            google_app, created = SocialApp.objects.get_or_create(
                provider='google',
                defaults={
                    'name': 'Google OAuth',
                    'client_id': client_id,
                    'secret': secret,
                }
            )

            # Always update the sites (in case user is reconfiguring)
            if not created:
                google_app.client_id = client_id
                google_app.secret = secret
                google_app.save()
                self.stdout.write(
                    self.style.WARNING('Updated existing Google OAuth app')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('Created Google OAuth app')
                )

            # Add site to the app
            google_app.sites.add(site)

            self.stdout.write(
                self.style.SUCCESS('✓ Google OAuth is now configured!')
            )
            self.stdout.write(
                self.style.SUCCESS(f'✓ Domain: {domain}')
            )
            self.stdout.write(
                self.style.SUCCESS(f'✓ Client ID: {client_id[:20]}...')
            )
            self.stdout.write('')
            self.stdout.write('Next steps:')
            self.stdout.write('1. Start the server: python manage.py runserver')
            self.stdout.write('2. Go to http://localhost:8000/auth/login/')
            self.stdout.write('3. Click "Sign in with Google" to test')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )
