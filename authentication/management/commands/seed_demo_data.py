from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.utils import timezone

from authentication.models import (
    ActivityLog,
    Booking,
    BookingStatus,
    Complaint,
    ComplaintStatus,
    CustomUser,
    Payment,
    PaymentMethod,
    PaymentStatus,
    Room,
    RoomStatus,
    RoomType,
    Testimonial,
    UserRole,
)


DEMO_PASSWORD = 'Demo@1234'


class Command(BaseCommand):
    help = 'Seed realistic Cebu Mini Hotel demo data for capstone presentations.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Clear existing demo users/bookings/payments/testimonials/complaints/activity logs first.',
        )

    def handle(self, *args, **options):
        self._ensure_testimonial_schema()

        with transaction.atomic():
            self._seed_all(options)

        self.stdout.write(self.style.SUCCESS('Demo data seeded successfully.'))
        self.stdout.write('Run again safely, or use --reset to rebuild demo rows.')

    def _seed_all(self, options):
        if options['reset']:
            self._reset_demo_data()

        guests = self._seed_guests()
        staff, manager, admin = self._seed_demo_staff()
        rooms = self._seed_rooms()
        bookings = self._seed_bookings(guests, rooms)
        self._seed_payments(bookings)
        self._sync_room_states(rooms, bookings)
        self._seed_testimonials(guests)
        self._seed_complaints(guests, bookings, staff, manager)
        self._seed_activity_logs(staff, manager, admin, bookings)

    def _ensure_testimonial_schema(self):
        """
        Repair older local demo DBs where migration 0019 is marked applied but
        testimonial review columns are missing.
        """
        existing_columns = {
            column.name for column in connection.introspection.get_table_description(
                connection.cursor(),
                Testimonial._meta.db_table,
            )
        }
        missing_fields = [
            field
            for field in [
                Testimonial._meta.get_field('content'),
                Testimonial._meta.get_field('status'),
                Testimonial._meta.get_field('reviewed_by'),
                Testimonial._meta.get_field('reviewed_at'),
            ]
            if field.column not in existing_columns
        ]
        if not missing_fields:
            return

        with connection.schema_editor() as schema_editor:
            for field in missing_fields:
                schema_editor.add_field(Testimonial, field)

    def _reset_demo_data(self):
        demo_emails = [
            'juan@demo.com',
            'maria@demo.com',
            'pedro@demo.com',
            'staff@demo.com',
            'manager@demo.com',
            'admin@demo.com',
        ]
        demo_bookings = Booking.objects.filter(booking_reference__startswith='DEMO-')
        Payment.objects.filter(booking__in=demo_bookings).delete()
        Complaint.objects.filter(guest__email__in=demo_emails).delete()
        Testimonial.objects.filter(guest_email__in=demo_emails).delete()
        ActivityLog.objects.filter(target__startswith='Demo ').delete()
        demo_bookings.delete()
        CustomUser.objects.filter(email__in=demo_emails).delete()

    def _seed_guests(self):
        guest_specs = [
            ('juan', 'Juan', 'dela Cruz', 'juan@demo.com', '09171234567'),
            ('maria', 'Maria', 'Santos', 'maria@demo.com', '09181234567'),
            ('pedro', 'Pedro', 'Reyes', 'pedro@demo.com', '09191234567'),
        ]
        guests = {}
        for username, first_name, last_name, email, phone in guest_specs:
            user, _ = CustomUser.objects.update_or_create(
                email=email,
                defaults={
                    'username': username,
                    'first_name': first_name,
                    'last_name': last_name,
                    'phone_number': phone,
                    'role': UserRole.GUEST,
                    'is_email_verified': True,
                    'terms_accepted': True,
                    'terms_accepted_at': timezone.now(),
                    'terms_version': '1.0',
                },
            )
            user.set_password(DEMO_PASSWORD)
            user.save()
            guests[email] = user
        return guests

    def _seed_demo_staff(self):
        users = []
        for username, email, first_name, last_name, role in [
            ('demo_staff', 'staff@demo.com', 'Ana', 'Lim', UserRole.STAFF),
            ('demo_manager', 'manager@demo.com', 'Carlo', 'Mendoza', UserRole.MANAGER),
            ('demo_admin', 'admin@demo.com', 'Liza', 'Garcia', UserRole.ADMIN),
        ]:
            user, _ = CustomUser.objects.update_or_create(
                email=email,
                defaults={
                    'username': username,
                    'first_name': first_name,
                    'last_name': last_name,
                    'role': role,
                    'is_staff': role in [UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN],
                    'is_superuser': role == UserRole.ADMIN,
                    'is_email_verified': True,
                    'terms_accepted': True,
                    'terms_accepted_at': timezone.now(),
                    'terms_version': '1.0',
                },
            )
            user.set_password(DEMO_PASSWORD)
            user.save()
            users.append(user)
        return users

    def _seed_rooms(self):
        room_specs = [
            ('101', RoomType.STANDARD, Decimal('1200.00'), 2, 'Queen bed, Wi-Fi, hot shower'),
            ('102', RoomType.STANDARD, Decimal('1200.00'), 2, 'Twin beds, Wi-Fi, work desk'),
            ('201', RoomType.DELUXE, Decimal('2500.00'), 3, 'City view, minibar, smart TV'),
            ('202', RoomType.DELUXE, Decimal('2500.00'), 3, 'Balcony, minibar, smart TV'),
            ('301', RoomType.SUITE, Decimal('5500.00'), 4, 'Living area, ocean view, breakfast'),
            ('302', RoomType.SUITE, Decimal('5500.00'), 4, 'Family suite, kitchenette, breakfast'),
        ]
        rooms = {}
        for number, room_type, price, capacity, amenities in room_specs:
            room, _ = Room.objects.update_or_create(
                room_number=number,
                defaults={
                    'room_type': room_type,
                    'price_per_night': price,
                    'capacity': capacity,
                    'amenities': amenities,
                    'description': f'{RoomType(room_type).label} with Cebu Mini Hotel essentials.',
                    'is_available': True,
                    'status': RoomStatus.CLEAN,
                },
            )
            rooms[number] = room
        return rooms

    def _seed_bookings(self, guests, rooms):
        today = timezone.now().date()
        specs = [
            ('DEMO-OUT1', rooms['101'], guests['juan@demo.com'], today - timedelta(days=18), today - timedelta(days=15), BookingStatus.CHECKED_OUT),
            ('DEMO-OUT2', rooms['201'], guests['maria@demo.com'], today - timedelta(days=12), today - timedelta(days=10), BookingStatus.CHECKED_OUT),
            ('DEMO-IN1', rooms['102'], guests['pedro@demo.com'], today - timedelta(days=1), today + timedelta(days=2), BookingStatus.CHECKED_IN),
            ('DEMO-IN2', rooms['202'], guests['juan@demo.com'], today, today + timedelta(days=3), BookingStatus.CHECKED_IN),
            ('DEMO-CON1', rooms['301'], guests['maria@demo.com'], today + timedelta(days=8), today + timedelta(days=10), BookingStatus.CONFIRMED),
            ('DEMO-CON2', rooms['302'], guests['pedro@demo.com'], today + timedelta(days=14), today + timedelta(days=17), BookingStatus.CONFIRMED),
            ('DEMO-PEND1', rooms['101'], guests['juan@demo.com'], today + timedelta(days=24), today + timedelta(days=26), BookingStatus.PENDING),
            ('DEMO-CAN1', rooms['201'], guests['maria@demo.com'], today + timedelta(days=28), today + timedelta(days=30), BookingStatus.CANCELLED),
        ]
        bookings = {}
        for reference, room, guest, check_in, check_out, status in specs:
            booking, _ = Booking.objects.update_or_create(
                booking_reference=reference,
                defaults={
                    'room': room,
                    'guest': guest,
                    'check_in': check_in,
                    'check_out': check_out,
                    'total_price': (check_out - check_in).days * room.price_per_night,
                    'status': status,
                    'special_requests': 'Demo presentation booking',
                    'checked_in_at': timezone.now() - timedelta(hours=4) if status == BookingStatus.CHECKED_IN else None,
                    'checked_out_at': timezone.now() - timedelta(days=10) if status == BookingStatus.CHECKED_OUT else None,
                    'cancelled_at': timezone.now() - timedelta(days=1) if status == BookingStatus.CANCELLED else None,
                    'cancellation_reason': 'Guest requested cancellation' if status == BookingStatus.CANCELLED else None,
                },
            )
            bookings[reference] = booking
        return bookings

    def _seed_payments(self, bookings):
        for reference, booking in bookings.items():
            if reference == 'DEMO-PEND1':
                continue

            status = PaymentStatus.REFUND_PENDING if reference == 'DEMO-CAN1' else PaymentStatus.COMPLETED
            completed_at = None if status == PaymentStatus.REFUND_PENDING else timezone.now() - timedelta(days=2)
            Payment.objects.update_or_create(
                booking=booking,
                reference_number=f'DEMO-PAY-{reference}',
                defaults={
                    'amount': booking.total_price,
                    'payment_method': PaymentMethod.PAYMONGO if reference != 'DEMO-CAN1' else PaymentMethod.CASH,
                    'status': status,
                    'transaction_id': f'txn_{reference.lower().replace("-", "_")}' if status == PaymentStatus.COMPLETED else None,
                    'completed_at': completed_at,
                    'notes': 'Demo completed payment' if status == PaymentStatus.COMPLETED else 'Demo cancellation awaiting refund review',
                },
            )

    def _sync_room_states(self, rooms, bookings):
        occupied_room_ids = {
            booking.room_id
            for booking in bookings.values()
            if booking.status == BookingStatus.CHECKED_IN
        }
        for room in rooms.values():
            if room.id in occupied_room_ids:
                room.is_available = False
                room.status = RoomStatus.OCCUPIED
            else:
                room.is_available = True
                room.status = RoomStatus.CLEAN
            room.save(update_fields=['is_available', 'status', 'updated_at'])

    def _seed_testimonials(self, guests):
        specs = [
            (guests['juan@demo.com'], 5, 'Perfect Cebu stay', 'Clean rooms, fast check-in, and very helpful staff.'),
            (guests['maria@demo.com'], 4, 'Comfortable and convenient', 'The location made our itinerary easy and the room felt fresh.'),
            (guests['pedro@demo.com'], 5, 'Great value', 'Smooth booking and payment flow, plus friendly front desk support.'),
        ]
        for guest, rating, title, comment in specs:
            Testimonial.objects.update_or_create(
                guest_email=guest.email,
                title=title,
                defaults={
                    'guest': guest,
                    'guest_name': guest.get_full_name(),
                    'rating': rating,
                    'comment': comment,
                    'is_approved': True,
                },
            )

    def _seed_complaints(self, guests, bookings, staff, manager):
        Complaint.objects.update_or_create(
            guest=guests['juan@demo.com'],
            subject='Aircon was noisy',
            defaults={
                'booking': bookings['DEMO-OUT1'],
                'description': 'The aircon made a rattling sound during the first night.',
                'status': ComplaintStatus.RESOLVED,
                'assigned_to': staff,
                'escalated_to': manager,
                'staff_notes': 'Maintenance inspected the unit.',
                'resolution_notes': 'Room aircon cleaned and guest was offered late checkout.',
                'resolved_at': timezone.now() - timedelta(days=12),
            },
        )
        Complaint.objects.update_or_create(
            guest=guests['pedro@demo.com'],
            subject='Extra towel request pending',
            defaults={
                'booking': bookings['DEMO-IN1'],
                'description': 'Guest requested additional towels for current stay.',
                'status': ComplaintStatus.PENDING,
                'assigned_to': staff,
                'staff_notes': 'Queued for housekeeping delivery.',
            },
        )

    def _seed_activity_logs(self, staff, manager, admin, bookings):
        specs = [
            (staff, 'Checked in current guest', f'Demo Booking {bookings["DEMO-IN1"].booking_reference}'),
            (staff, 'Confirmed room housekeeping status', 'Demo Room 102'),
            (manager, 'Reviewed pending refund', f'Demo Booking {bookings["DEMO-CAN1"].booking_reference}'),
            (admin, 'Reviewed payment collection dashboard', 'Demo Payment Collection'),
            (staff, 'Recorded guest service complaint', 'Demo Complaint: Extra towel request pending'),
        ]
        for index, (user, action, target) in enumerate(specs):
            log, _ = ActivityLog.objects.update_or_create(
                action=action,
                target=target,
                defaults={'user': user, 'ip_address': '127.0.0.1'},
            )
            ActivityLog.objects.filter(pk=log.pk).update(
                timestamp=timezone.now() - timedelta(hours=index + 1)
            )
