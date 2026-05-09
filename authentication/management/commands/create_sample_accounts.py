from django.core.management.base import BaseCommand
from django.utils import timezone
from authentication.models import CustomUser, UserRole


class Command(BaseCommand):
    help = 'Create sample user accounts for each entity role (Admin, Manager, Staff, Guest).'

    SAMPLE_USERS = [
        {
            'username': 'admin_super',
            'email': 'admin@example.com',
            'first_name': 'Super',
            'last_name': 'Admin',
            'role': UserRole.ADMIN,
            'password': 'AdminPass123!',
            'is_staff': True,
            'is_superuser': True,
        },
        {
            'username': 'manager_alex',
            'email': 'alex.manager@example.com',
            'first_name': 'Alex',
            'last_name': 'Taylor',
            'role': UserRole.MANAGER,
            'password': 'ManagerPass123!',
            'is_staff': True,
            'is_superuser': False,
        },
        {
            'username': 'staff_emily',
            'email': 'emily.staff@example.com',
            'first_name': 'Emily',
            'last_name': 'Davis',
            'role': UserRole.STAFF,
            'password': 'StaffPass123!',
            'is_staff': True,
            'is_superuser': False,
        },
        {
            'username': 'guest_john',
            'email': 'john.guest@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'role': UserRole.GUEST,
            'password': 'GuestPass123!',
            'is_staff': False,
            'is_superuser': False,
        },
    ]

    def handle(self, *args, **options):
        for user_data in self.SAMPLE_USERS:
            user, created = CustomUser.objects.get_or_create(
                email=user_data['email'],
                defaults={
                    'username': user_data['username'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'role': user_data['role'],
                    'is_staff': user_data['is_staff'],
                    'is_superuser': user_data['is_superuser'],
                    'is_active': True,
                    'is_email_verified': True,
                    'terms_accepted': True,
                    'terms_accepted_at': timezone.now(),
                    'terms_version': '1.0',
                }
            )

            user.username = user_data['username']
            user.first_name = user_data['first_name']
            user.last_name = user_data['last_name']
            user.role = user_data['role']
            user.is_staff = user_data['is_staff']
            user.is_superuser = user_data['is_superuser']
            user.is_active = True
            user.is_email_verified = True
            user.terms_accepted = True
            user.terms_accepted_at = timezone.now()
            user.terms_version = '1.0'
            user.set_password(user_data['password'])
            user.save()

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created sample user: {user.email} ({user.role})"))
            else:
                self.stdout.write(self.style.WARNING(f"Updated sample user: {user.email} ({user.role})"))

        self.stdout.write(self.style.SUCCESS('Sample accounts creation completed.'))
