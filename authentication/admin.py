from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Q, Sum, Count
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import CustomUser, UserRole, TermsAndConditions, Room, RoomImage, Booking, BookingStatus, RoomType, ContactMessage
import json


# Custom Filters
class ActiveRoomsFilter(admin.SimpleListFilter):
    """Filter for active/inactive rooms"""
    title = 'Room Status'
    parameter_name = 'room_active'
    
    def lookups(self, request, model_admin):
        return (
            ('available', 'Available'),
            ('unavailable', 'Unavailable'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'available':
            return queryset.filter(is_available=True)
        if self.value() == 'unavailable':
            return queryset.filter(is_available=False)
        return queryset


class PriceRangeFilter(admin.SimpleListFilter):
    """Filter for price ranges"""
    title = 'Price Range'
    parameter_name = 'price_range'
    
    def lookups(self, request, model_admin):
        return (
            ('budget', '< ₱2,000'),
            ('standard', '₱2,000 - ₱3,500'),
            ('premium', '₱3,500 - ₱5,000'),
            ('luxury', '> ₱5,000'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'budget':
            return queryset.filter(price_per_night__lt=2000)
        if self.value() == 'standard':
            return queryset.filter(price_per_night__gte=2000, price_per_night__lt=3500)
        if self.value() == 'premium':
            return queryset.filter(price_per_night__gte=3500, price_per_night__lt=5000)
        if self.value() == 'luxury':
            return queryset.filter(price_per_night__gte=5000)
        return queryset


class BookingStatusFilter(admin.SimpleListFilter):
    """Filter for booking statuses"""
    title = 'Booking Status'
    parameter_name = 'booking_status'
    
    def lookups(self, request, model_admin):
        return (
            ('CONFIRMED', '✓ Confirmed'),
            ('PENDING', '⏳ Pending'),
            ('CANCELLED', '✗ Cancelled'),
        )
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Custom User Admin with enhanced filtering and search"""
    model = CustomUser
    list_display = ('username', 'email', 'full_name', 'role_badge', 'terms_status', 'is_active', 'created_at')
    list_filter = ('role', 'terms_accepted', 'is_active', 'is_staff', 'created_at')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')
    readonly_fields = ('created_at', 'updated_at', 'terms_accepted_at', 'booking_summary')
    ordering = ('-created_at',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'phone_number')}),
        ('Role & Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Terms & Conditions', {'fields': ('terms_accepted', 'terms_accepted_at', 'terms_version')}),
        ('Email Verification', {'fields': ('is_email_verified',)}),
        ('Booking Summary', {'fields': ('booking_summary',), 'classes': ('collapse',)}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role'),
        }),
    )

    def role_badge(self, obj):
        """Display role as colored badge"""
        if obj.is_admin():
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">Admin</span>'
            )
        return format_html(
            '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">Guest</span>'
        )
    role_badge.short_description = 'Role'

    def full_name(self, obj):
        """Display full name or username"""
        return obj.get_full_name() or obj.username
    full_name.short_description = 'Name'

    def terms_status(self, obj):
        """Display terms acceptance status"""
        if obj.terms_accepted:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Accepted</span>'
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">✗ Not Accepted</span>'
        )
    terms_status.short_description = 'T&C Status'

    def booking_summary(self, obj):
        """Show booking statistics for user"""
        bookings = Booking.objects.filter(guest=obj)
        confirmed = bookings.filter(status='CONFIRMED').count()
        total_spent = bookings.filter(status='CONFIRMED').aggregate(Sum('total_price'))['total_price__sum'] or 0
        
        return format_html(
            '<strong>Total Bookings:</strong> {}<br/>'
            '<strong>Confirmed:</strong> {}<br/>'
            '<strong>Total Spent:</strong> ₱{:,}',
            bookings.count(),
            confirmed,
            total_spent
        )
    booking_summary.short_description = 'Booking Summary'


@admin.register(TermsAndConditions)
class TermsAndConditionsAdmin(admin.ModelAdmin):
    """Terms and Conditions Admin"""
    list_display = ('version', 'active_status', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('version', 'content')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Version Info', {'fields': ('version', 'is_active')}),
        ('Content', {'fields': ('content',), 'classes': ('wide',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

    def active_status(self, obj):
        """Display active status"""
        if obj.is_active:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Active</span>'
            )
        return format_html(
            '<span style="color: gray;">Inactive</span>'
        )
    active_status.short_description = 'Status'

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of T&C records"""
        return False


class RoomImageInline(admin.TabularInline):
    """Inline admin for room images"""
    model = RoomImage
    extra = 1
    fields = ('image', 'caption')
    readonly_fields = ('uploaded_at',)


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    """Room Admin with enhanced filtering, search, and display"""
    list_display = ('room_number', 'room_type_display', 'capacity_display', 'price_display', 'availability_status', 'occupancy_rate', 'created_at')
    list_filter = (ActiveRoomsFilter, PriceRangeFilter, 'room_type', 'capacity', 'created_at')
    search_fields = ('room_number', 'description', 'amenities')
    readonly_fields = ('created_at', 'updated_at', 'occupancy_info', 'revenue_info')
    inlines = [RoomImageInline]
    ordering = ('room_number',)

    fieldsets = (
        ('Room Info', {'fields': ('room_number', 'room_type', 'description')}),
        ('Pricing & Capacity', {'fields': ('price_per_night', 'capacity')}),
        ('Status', {'fields': ('is_available',)}),
        ('Details', {'fields': ('amenities', 'image')}),
        ('Statistics', {'fields': ('occupancy_info', 'revenue_info'), 'classes': ('collapse',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

    def room_type_display(self, obj):
        """Display room type with color"""
        colors = {
            'STANDARD': '#007bff',
            'DELUXE': '#28a745',
            'PREMIUM': '#ffc107',
            'SUITE': '#e83e8c',
        }
        color = colors.get(obj.room_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_room_type_display()
        )
    room_type_display.short_description = 'Type'

    def capacity_display(self, obj):
        """Display capacity with guest icons"""
        return format_html(
            '👤 × {}',
            obj.capacity
        )
    capacity_display.short_description = 'Capacity'

    def price_display(self, obj):
        """Display price formatted"""
        return format_html(
            '₱{:,}',
            obj.price_per_night
        )
    price_display.short_description = 'Price/Night'

    def availability_status(self, obj):
        """Display availability as badge"""
        if obj.is_available:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">Available</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px;">Unavailable</span>'
        )
    availability_status.short_description = 'Availability'

    def occupancy_rate(self, obj):
        """Calculate occupancy rate"""
        from django.utils import timezone
        from datetime import timedelta
        
        today = timezone.now().date()
        bookings_this_month = Booking.objects.filter(
            room=obj,
            check_in__month=today.month,
            check_in__year=today.year,
            status='CONFIRMED'
        ).count()
        
        occupancy_percent = min((bookings_this_month / 30) * 100, 100)
        
        if occupancy_percent >= 80:
            color = '#28a745'
        elif occupancy_percent >= 50:
            color = '#ffc107'
        else:
            color = '#dc3545'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.0f}%</span>',
            color,
            occupancy_percent
        )
    occupancy_rate.short_description = 'Occupancy %'

    def occupancy_info(self, obj):
        """Show detailed occupancy information"""
        bookings = Booking.objects.filter(room=obj, status='CONFIRMED')
        total_bookings = bookings.count()
        total_revenue = bookings.aggregate(Sum('total_price'))['total_price__sum'] or 0
        
        return format_html(
            '<strong>Total Bookings:</strong> {}<br/>'
            '<strong>Total Revenue:</strong> ₱{:,}<br/>',
            total_bookings,
            total_revenue
        )
    occupancy_info.short_description = 'Occupancy Info'

    def revenue_info(self, obj):
        """Show revenue information"""
        bookings = Booking.objects.filter(room=obj, status='CONFIRMED')
        total_revenue = bookings.aggregate(Sum('total_price'))['total_price__sum'] or 0
        avg_booking = bookings.aggregate(avg=Sum('total_price') / Count('id'))['avg'] or 0
        
        return format_html(
            '<strong>Total Revenue:</strong> ₱{:,}<br/>'
            '<strong>Average per Booking:</strong> ₱{:,}<br/>',
            total_revenue,
            int(avg_booking)
        )
    revenue_info.short_description = 'Revenue Info'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)


@admin.register(RoomImage)
class RoomImageAdmin(admin.ModelAdmin):
    """Room Image Admin"""
    list_display = ('room', 'caption_preview', 'image_preview', 'uploaded_at')
    list_filter = ('room', 'uploaded_at')
    search_fields = ('room__room_number', 'caption')
    readonly_fields = ('uploaded_at', 'image_preview')
    ordering = ('-uploaded_at',)

    fieldsets = (
        ('Image Info', {'fields': ('room', 'caption')}),
        ('File', {'fields': ('image', 'image_preview')}),
        ('Uploaded', {'fields': ('uploaded_at',)}),
    )

    def caption_preview(self, obj):
        """Show caption or 'No caption'"""
        return obj.caption or '(No caption)'
    caption_preview.short_description = 'Caption'

    def image_preview(self, obj):
        """Show image preview"""
        if obj.image:
            return format_html(
                '<img src="{}" width="200" />',
                obj.image.url
            )
        return '(No image)'
    image_preview.short_description = 'Preview'


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """Booking Admin with enhanced filtering and search"""
    list_display = ('booking_id', 'guest_info', 'room_info', 'dates_info', 'price_display', 'status_badge', 'created_at')
    list_filter = (BookingStatusFilter, 'room__room_type', 'check_in', 'created_at')
    search_fields = ('id', 'room__room_number', 'guest__username', 'guest__email', 'guest__first_name')
    readonly_fields = ('created_at', 'updated_at', 'total_price', 'duration_info')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Booking Info', {'fields': ('id', 'status')}),
        ('Guest', {'fields': ('guest',)}),
        ('Room', {'fields': ('room',)}),
        ('Stay Dates', {'fields': ('check_in', 'check_out', 'duration_info')}),
        ('Pricing', {'fields': ('total_price',)}),
        ('Special Requests', {'fields': ('special_requests',), 'classes': ('wide',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

    def booking_id(self, obj):
        """Display booking ID"""
        return format_html(
            '<strong>#{}</strong>',
            obj.id
        )
    booking_id.short_description = 'ID'

    def guest_info(self, obj):
        """Display guest information"""
        return format_html(
            '{}<br/><small style="color: #666;">{}</small>',
            obj.guest.get_full_name() or obj.guest.username,
            obj.guest.email
        )
    guest_info.short_description = 'Guest'

    def room_info(self, obj):
        """Display room information"""
        return format_html(
            'Room {}<br/><small style="color: #666;">{}</small>',
            obj.room.room_number,
            obj.room.get_room_type_display()
        )
    room_info.short_description = 'Room'

    def dates_info(self, obj):
        """Display check-in and check-out dates"""
        return format_html(
            '{}<br/>to<br/>{}',
            obj.check_in.strftime('%b %d, %Y'),
            obj.check_out.strftime('%b %d, %Y')
        )
    dates_info.short_description = 'Dates'

    def price_display(self, obj):
        """Display total price"""
        return format_html(
            '₱{:,}',
            obj.total_price
        )
    price_display.short_description = 'Total Price'

    def status_badge(self, obj):
        """Display status as colored badge"""
        colors = {
            'CONFIRMED': '#28a745',
            'PENDING': '#ffc107',
            'CANCELLED': '#dc3545',
        }
        icons = {
            'CONFIRMED': '✓',
            'PENDING': '⏳',
            'CANCELLED': '✗',
        }
        color = colors.get(obj.status, '#6c757d')
        icon = icons.get(obj.status, '?')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold;">{} {}</span>',
            color,
            icon,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def duration_info(self, obj):
        """Show booking duration"""
        duration = (obj.check_out - obj.check_in).days
        return format_html(
            '<strong>{} night{}</strong>',
            duration,
            's' if duration != 1 else ''
        )
    duration_info.short_description = 'Duration'

    def has_add_permission(self, request):
        """Disable manual booking creation in admin"""
        return False

    def save_model(self, request, obj, form, change):
        # Recalculate price when saving
        if not obj.total_price or obj.total_price == 0:
            obj.total_price = obj.calculate_total_price()
        super().save_model(request, obj, form, change)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    """Contact Message Admin with notification actions"""
    list_display = ('subject_preview', 'sender_info', 'status_badge', 'reply_status', 'created_at')
    list_filter = ('is_read', 'is_replied', 'notification_sent', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('created_at', 'updated_at', 'message_preview')
    ordering = ('-created_at',)
    actions = ['mark_as_read', 'mark_as_replied_and_notify']
    
    fieldsets = (
        ('Message Info', {'fields': ('name', 'email', 'phone', 'subject')}),
        ('Content', {'fields': ('message', 'message_preview'), 'classes': ('wide',)}),
        ('Guest Link', {'fields': ('guest',)}),
        ('Status', {'fields': ('is_read', 'is_replied')}),
        ('Staff Response', {'fields': ('staff_response',), 'classes': ('wide',)}),
        ('Notifications', {'fields': ('notification_sent', 'last_notified_at')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

    def subject_preview(self, obj):
        """Display subject preview"""
        return obj.subject[:50] + '...' if len(obj.subject) > 50 else obj.subject
    subject_preview.short_description = 'Subject'

    def sender_info(self, obj):
        """Display sender name and email"""
        return format_html(
            '{}<br/><small style="color: #666;">{}</small>',
            obj.name,
            obj.email
        )
    sender_info.short_description = 'From'

    def status_badge(self, obj):
        """Display read/unread status"""
        if obj.is_read:
            return format_html(
                '<span style="background-color: #d1d5db; color: #374151; padding: 3px 10px; border-radius: 3px;">✓ Read</span>'
            )
        return format_html(
            '<span style="background-color: #fbbf24; color: #78350f; padding: 3px 10px; border-radius: 3px;">Unread</span>'
        )
    status_badge.short_description = 'Status'

    def reply_status(self, obj):
        """Display reply status with notification indicator"""
        if obj.is_replied:
            if obj.notification_sent:
                return format_html(
                    '<span style="background-color: #d1fae5; color: #065f46; padding: 3px 10px; border-radius: 3px;">✓ Replied & Notified</span>'
                )
            else:
                return format_html(
                    '<span style="background-color: #dbeafe; color: #0c4a6e; padding: 3px 10px; border-radius: 3px;">⚠ Replied (Not Notified)</span>'
                )
        return format_html(
            '<span style="background-color: #fee2e2; color: #7f1d1d; padding: 3px 10px; border-radius: 3px;">Pending</span>'
        )
    reply_status.short_description = 'Reply Status'

    def message_preview(self, obj):
        """Display full message for readonly"""
        return obj.message
    message_preview.short_description = 'Full Message'

    def mark_as_read(self, request, queryset):
        """Action to mark messages as read"""
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} message(s) marked as read.')
    mark_as_read.short_description = 'Mark selected as read'

    def mark_as_replied_and_notify(self, request, queryset):
        """Action to mark as replied and send notification email"""
        count = 0
        for message in queryset:
            if message.guest and message.guest.email:
                message.is_replied = True
                message.save()
                message.send_reply_notification()
                count += 1
        
        self.message_user(request, f'{count} message(s) marked as replied and guest notification email(s) sent.')
    mark_as_replied_and_notify.short_description = 'Mark as replied & send notification email to guest'

