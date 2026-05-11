from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.db import IntegrityError
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.http import require_GET, require_POST
from datetime import datetime
from decimal import Decimal

from .models import (
    Booking, Room, BookingStatus, Payment, PaymentStatus,
    Complaint, ComplaintStatus, GuestComplaintEscalation, RefundRequest, RefundRequestStatus
)
from .forms_bookings import (
    BookingForm, BookingFilterForm, BookingConfirmationForm
)
from .views_recommendations import get_recommendations_context
from .decorators import guest_required, admin_required
from .emails import send_cancellation_email


# ==================== GUEST VIEWS ====================

@login_required(login_url='auth:login')
@guest_required
def create_booking_view(request, room_id):
    """Create a new booking for a room"""
    room = get_object_or_404(Room, id=room_id)
    
    if request.method == 'POST':
        # First step: submit dates
        form = BookingForm(request.POST, room=room)
        
        if form.is_valid():
            # Store in session for confirmation step
            request.session['booking_data'] = {
                'room_id': room_id,
                'check_in': form.cleaned_data['check_in'].isoformat(),
                'check_out': form.cleaned_data['check_out'].isoformat(),
                'special_requests': form.cleaned_data['special_requests'],
            }
            
            # Calculate total price for display
            duration = (form.cleaned_data['check_out'] - form.cleaned_data['check_in']).days
            total_price = duration * room.price_per_night
            request.session['booking_price'] = str(total_price)
            
            return redirect('bookings:confirm_booking')
    else:
        form = BookingForm(
            room=room,
            initial={
                'check_in': request.GET.get('check_in') or None,
                'check_out': request.GET.get('check_out') or None,
            }
        )
    
    # Get unavailable date ranges for flatpickr and occupied dates for fallback display.
    occupied_dates = []
    booked_date_ranges = []
    bookings = Booking.objects.filter(
        room=room,
        status__in=[BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN]
    )
    for booking in bookings:
        booked_date_ranges.append({
            'from': booking.check_in.isoformat(),
            'to': (booking.check_out - timezone.timedelta(days=1)).isoformat(),
        })
        current_date = booking.check_in
        while current_date < booking.check_out:
            occupied_dates.append(current_date.isoformat())
            current_date = current_date + timezone.timedelta(days=1)

    context = {
        'form': form,
        'room': room,
        'occupied_dates': occupied_dates,
        'booked_date_ranges': booked_date_ranges,
    }
    return render(request, 'bookings/create_booking.html', context)


@login_required(login_url='auth:login')
def confirm_booking_view(request):
    """Confirm booking before finalizing"""
    booking_data = request.session.get('booking_data')
    
    if not booking_data:
        messages.error(request, 'Invalid booking session. Please start over.')
        return redirect('rooms:list')
    
    room = get_object_or_404(Room, id=booking_data['room_id'])
    check_in = datetime.fromisoformat(booking_data['check_in']).date()
    check_out = datetime.fromisoformat(booking_data['check_out']).date()
    duration = (check_out - check_in).days
    total_price = duration * room.price_per_night
    
    if request.method == 'POST':
        confirmation_form = BookingConfirmationForm(request.POST)
        
        if confirmation_form.is_valid():
            # Create booking with PENDING status (payment required before confirmation)
            booking = Booking.objects.create(
                room=room,
                guest=request.user,
                check_in=check_in,
                check_out=check_out,
                total_price=total_price,
                special_requests=booking_data.get('special_requests', ''),
                status=BookingStatus.PENDING  # Changed from CONFIRMED to PENDING
            )
            
            # Clear session
            del request.session['booking_data']
            if 'booking_price' in request.session:
                del request.session['booking_price']
            
            messages.info(
                request, 
                'Booking created! Please proceed to payment to confirm your reservation.'
            )
            # Create Payment record for PayMongo
            Payment.objects.get_or_create(
                booking=booking,
                defaults={
                    'amount': booking.total_price,
                    'payment_method': 'PAYMONGO',
                    'status': PaymentStatus.PENDING
                }
            )
            
            # Redirect directly to PayMongo payment
            return redirect('bookings:paymongo_payment', booking_id=booking.id)
    else:
        confirmation_form = BookingConfirmationForm()
    
    # Get recommendations for other rooms
    recommendations_context = get_recommendations_context(
        request, 
        exclude_room_id=room.id,
        limit=3
    )
    
    context = {
        'room': room,
        'check_in': check_in,
        'check_out': check_out,
        'duration': duration,
        'total_price': total_price,
        'special_requests': booking_data.get('special_requests', ''),
        'confirmation_form': confirmation_form,
        'recommendations': recommendations_context['recommendations'],
        'has_recommendations': recommendations_context['has_recommendations'],
    }
    return render(request, 'bookings/confirm_booking.html', context)


@login_required(login_url='auth:login')
def booking_detail_view(request, booking_id):
    """View booking details"""
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Check authorization: guest can only view their own bookings
    if request.user != booking.guest and not request.user.is_admin():
        messages.error(request, 'You do not have permission to view this booking.')
        return redirect('rooms:list')
    
    can_cancel = booking.can_be_cancelled()
    completed_payment = (
        Payment.objects
        .filter(booking=booking, status=PaymentStatus.COMPLETED)
        .order_by('-completed_at', '-created_at')
        .first()
    )
    existing_refund = RefundRequest.objects.filter(booking=booking).first()
    can_request_refund = completed_payment is not None and existing_refund is None
    
    # Get recommendations for this booking
    recommendations_context = get_recommendations_context(
        request,
        exclude_room_id=booking.room.id,
        limit=3
    )
    
    context = {
        'booking': booking,
        'can_cancel': can_cancel,
        'can_request_refund': can_request_refund,
        'existing_refund': existing_refund,
        'recommendations': recommendations_context['recommendations'],
        'has_recommendations': recommendations_context['has_recommendations'],
    }
    return render(request, 'bookings/booking_detail.html', context)


@login_required(login_url='auth:login')
@guest_required
def booking_history_view(request):
    """View guest's booking history"""
    bookings = Booking.objects.filter(guest=request.user).order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status', '')
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(bookings, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'bookings': page_obj.object_list,
        'status_filter': status_filter,
        'total_bookings': bookings.count(),
    }
    return render(request, 'bookings/booking_history.html', context)


@login_required(login_url='auth:login')
@guest_required
@require_POST
def cancel_booking_view(request, booking_id):
    """Cancel a guest booking and flag completed payments for refund review."""
    booking = get_object_or_404(Booking, id=booking_id, guest=request.user)

    if not booking.can_be_cancelled():
        messages.error(request, 'This booking cannot be cancelled.')
        return redirect('bookings:booking_detail', booking_id=booking_id)

    payment = (
        booking.payments.filter(status=PaymentStatus.COMPLETED).order_by('-completed_at', '-created_at').first()
        or booking.payments.order_by('-created_at').first()
    )
    booking.status = BookingStatus.CANCELLED
    booking.cancellation_reason = 'Cancelled by guest'
    booking.cancelled_at = timezone.now()
    booking.save(update_fields=['status', 'cancellation_reason', 'cancelled_at', 'updated_at'])

    if payment and payment.status == PaymentStatus.COMPLETED:
        payment.status = PaymentStatus.REFUND_PENDING
        payment.notes = 'Guest requested cancellation - refund pending review'
        payment.save(update_fields=['status', 'notes', 'updated_at'])
    elif payment and payment.status == PaymentStatus.PENDING:
        payment.status = PaymentStatus.CANCELLED
        payment.save(update_fields=['status', 'updated_at'])

    send_cancellation_email(booking, payment=payment)
    messages.success(request, f'Booking #{booking.id} has been cancelled successfully.')
    return redirect('auth:dashboard')


@login_required(login_url='auth:login')
@guest_required
@require_GET
def booking_pdf(request, booking_id):
    """Generate a guest-owned booking confirmation PDF."""
    from io import BytesIO

    booking = get_object_or_404(
        Booking.objects.select_related('guest', 'room').prefetch_related('payments'),
        id=booking_id,
    )

    if booking.guest_id != request.user.id:
        return HttpResponseForbidden('You do not have permission to download this booking confirmation.')

    try:
        import qrcode
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            Image,
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
    except ImportError as exc:
        return HttpResponse(
            f'PDF generation dependency is missing: {exc.name}. Please install reportlab and qrcode.',
            status=500,
            content_type='text/plain',
        )

    completed_payments = booking.payments.filter(status=PaymentStatus.COMPLETED)
    total_paid = sum((payment.amount for payment in completed_payments), Decimal('0'))
    payment = (
        completed_payments.order_by('-completed_at', '-created_at').first()
        or booking.payments.order_by('-created_at').first()
    )
    payment_method = payment.get_payment_method_display() if payment else 'N/A'
    payment_date = (
        (payment.completed_at or payment.updated_at or payment.created_at).strftime('%B %d, %Y')
        if payment else 'N/A'
    )
    guest_name = booking.guest.get_full_name() or booking.guest.username
    booking_reference = booking.booking_reference or f'BOOKING-{booking.id}'

    qr_buffer = BytesIO()
    qr = qrcode.QRCode(version=1, box_size=6, border=2)
    qr.add_data(str(booking.id))
    qr.make(fit=True)
    qr_image = qr.make_image(fill_color='#0f766e', back_color='white')
    qr_image.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        title=f'Cebu Mini Hotel Booking {booking.id}',
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CebuTitle',
        parent=styles['Title'],
        textColor=colors.HexColor('#0f766e'),
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        'CebuSubtitle',
        parent=styles['Normal'],
        textColor=colors.HexColor('#475569'),
        fontSize=10,
        alignment=TA_CENTER,
        spaceAfter=16,
    )
    section_style = ParagraphStyle(
        'CebuSection',
        parent=styles['Heading2'],
        textColor=colors.HexColor('#0f766e'),
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        spaceBefore=12,
        spaceAfter=8,
    )
    footer_style = ParagraphStyle(
        'CebuFooter',
        parent=styles['Normal'],
        textColor=colors.HexColor('#0f766e'),
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        fontSize=10,
    )

    logo_table = Table(
        [[Paragraph('<b>CMH</b>', ParagraphStyle(
            'LogoText',
            parent=styles['Normal'],
            textColor=colors.white,
            fontName='Helvetica-Bold',
            fontSize=14,
            alignment=TA_CENTER,
        ))]],
        colWidths=[0.8 * inch],
        rowHeights=[0.42 * inch],
        hAlign='CENTER',
    )
    logo_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#0f766e')),
        ('BOX', (0, 0), (-1, -1), 0, colors.HexColor('#0f766e')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    def details_table(rows):
        table = Table(rows, colWidths=[2.15 * inch, 4.2 * inch], hAlign='LEFT')
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('BOX', (0, 0), (-1, -1), 0.6, colors.HexColor('#d9e2e7')),
            ('INNERGRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#e5edf0')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#334155')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#111827')),
            ('FONTSIZE', (0, 0), (-1, -1), 9.5),
            ('LEADING', (0, 0), (-1, -1), 12),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        return table

    elements = [
        logo_table,
        Spacer(1, 0.12 * inch),
        Paragraph('Cebu Mini Hotel', title_style),
        Paragraph('Booking Confirmation', subtitle_style),
        details_table([
            ['Booking Reference Number', booking_reference],
            ['Booking ID', f'#{booking.id}'],
            ['Booking Status', booking.get_status_display()],
        ]),
        Paragraph('Guest Details', section_style),
        details_table([
            ['Full Name', guest_name],
            ['Email', booking.guest.email],
        ]),
        Paragraph('Stay Details', section_style),
        details_table([
            ['Room', f'Room {booking.room.room_number} - {booking.room.get_room_type_display()}'],
            ['Check-in Date', booking.check_in.strftime('%B %d, %Y')],
            ['Check-out Date', booking.check_out.strftime('%B %d, %Y')],
            ['Number of Nights', str(booking.get_duration())],
        ]),
        Paragraph('Payment Details', section_style),
        details_table([
            ['Total Amount Paid', f'PHP {total_paid:.2f}'],
            ['Payment Method', payment_method],
            ['Payment Date', payment_date],
        ]),
        Paragraph('Arrival QR Code', section_style),
    ]

    qr_table = Table(
        [[Image(qr_buffer, width=1.4 * inch, height=1.4 * inch),
          Paragraph('Staff may scan this QR code on arrival. It contains the booking ID for front desk verification.', styles['Normal'])]],
        colWidths=[1.65 * inch, 4.7 * inch],
    )
    qr_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.6, colors.HexColor('#d9e2e7')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.extend([
        qr_table,
        Spacer(1, 0.28 * inch),
        Paragraph('Thank you for choosing Cebu Mini Hotel', footer_style),
    ])

    doc.build(elements)
    buffer.seek(0)

    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="CebuMiniHotel_Booking_{booking.id}.pdf"'
    return response


# ==================== ADMIN VIEWS ====================

@login_required(login_url='auth:login')
def admin_bookings_view(request):
    """Admin view: list all bookings with filtering"""
    if not request.user.is_admin():
        messages.error(request, 'Admin access required.')
        return redirect('rooms:list')
    
    bookings = Booking.objects.select_related('room', 'guest').order_by('-created_at')
    
    # Apply filters
    filter_form = BookingFilterForm(request.GET)
    
    if filter_form.is_valid():
        # Room type filter
        room_type = filter_form.cleaned_data.get('room_type')
        if room_type:
            bookings = bookings.filter(room__room_type=room_type)
        
        # Status filter
        status = filter_form.cleaned_data.get('status')
        if status:
            bookings = bookings.filter(status=status)
        
        # Date range filters
        check_in_from = filter_form.cleaned_data.get('check_in_from')
        if check_in_from:
            bookings = bookings.filter(check_in__gte=check_in_from)
        
        check_in_to = filter_form.cleaned_data.get('check_in_to')
        if check_in_to:
            bookings = bookings.filter(check_in__lte=check_in_to)
        
        # Guest search
        guest_search = filter_form.cleaned_data.get('guest_search')
        if guest_search:
            bookings = bookings.filter(
                Q(guest__username__icontains=guest_search) |
                Q(guest__email__icontains=guest_search) |
                Q(guest__first_name__icontains=guest_search) |
                Q(guest__last_name__icontains=guest_search)
            )
    
    # Pagination
    paginator = Paginator(bookings, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Calculate statistics
    total_bookings = Booking.objects.count()
    confirmed_bookings = Booking.objects.filter(status=BookingStatus.CONFIRMED).count()
    pending_bookings = Booking.objects.filter(status=BookingStatus.PENDING).count()
    cancelled_bookings = Booking.objects.filter(status=BookingStatus.CANCELLED).count()
    
    # Revenue calculation
    revenue = sum(
        booking.total_price 
        for booking in Booking.objects.filter(status=BookingStatus.CONFIRMED)
    )
    
    context = {
        'page_obj': page_obj,
        'bookings': page_obj.object_list,
        'filter_form': filter_form,
        'total_bookings': total_bookings,
        'confirmed_bookings': confirmed_bookings,
        'pending_bookings': pending_bookings,
        'cancelled_bookings': cancelled_bookings,
        'revenue': revenue,
    }
    return render(request, 'bookings/admin_bookings.html', context)


@login_required(login_url='auth:login')
def admin_cancel_booking_view(request, booking_id):
    """Admin: cancel a booking"""
    if not request.user.is_admin():
        messages.error(request, 'Admin access required.')
        return redirect('rooms:list')
    
    booking = get_object_or_404(Booking, id=booking_id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        booking.status = BookingStatus.CANCELLED
        booking.save()
        
        messages.success(
            request,
            f'Booking #{booking.id} for {booking.guest.username} has been cancelled.'
        )
        return redirect('bookings:admin_bookings')
    
    context = {
        'booking': booking,
    }
    return render(request, 'bookings/admin_cancel_booking.html', context)


@login_required(login_url='auth:login')
def admin_confirm_booking_view(request, booking_id):
    """Admin: confirm a pending booking"""
    if not request.user.is_admin():
        messages.error(request, 'Admin access required.')
        return redirect('rooms:list')
    
    booking = get_object_or_404(Booking, id=booking_id)
    
    if booking.status != BookingStatus.PENDING:
        messages.warning(request, 'This booking is already confirmed or cancelled.')
        return redirect('bookings:admin_bookings')

    if not booking.payments.filter(status=PaymentStatus.COMPLETED).exists():
        messages.error(request, 'This booking cannot be confirmed until payment is completed.')
        return redirect('bookings:admin_bookings')
    
    booking.status = BookingStatus.CONFIRMED
    booking.save()
    
    messages.success(
        request,
        f'Booking #{booking.id} for {booking.guest.username} has been confirmed.'
    )
    return redirect('bookings:admin_bookings')


@login_required(login_url='auth:login')
def download_invoice_view(request, booking_id):
    """Guest or Admin can download booking invoice/receipt as PDF"""
    from django.http import FileResponse, HttpResponse
    from io import BytesIO
    from decimal import Decimal
    import os
    
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Check permissions: only guest, admin, or manager can download their/any invoice
    if (request.user != booking.guest and 
        not request.user.is_admin() and 
        not request.user.is_manager()):
        from django.contrib import messages
        messages.error(request, 'You do not have permission to download this invoice.')
        return redirect('home')
    
    # Try to generate PDF, fallback to HTML if reportlab not available
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib.units import inch
        from datetime import datetime
        import pytz
        
        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=0.5*inch, leftMargin=0.5*inch)
        elements = []
        
        styles = getSampleStyleSheet()
        
        # Title
        title = Paragraph(f"<b>BOOKING INVOICE</b>", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 0.3*inch))
        
        # Invoice details
        invoice_num = f"INV-{booking.id:05d}"
        invoice_date = booking.created_at.strftime('%Y-%m-%d %H:%M:%S')
        
        details_data = [
            ['Invoice Number:', invoice_num, 'Invoice Date:', invoice_date],
            ['Booking ID:', str(booking.id), 'Status:', booking.get_status_display()],
        ]
        
        details_table = Table(details_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        details_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ]))
        elements.append(details_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Guest information
        guest_info = Paragraph("<b>Guest Information:</b>", styles['Heading2'])
        elements.append(guest_info)
        
        guest_data = [
            ['Name:', f"{booking.guest.first_name} {booking.guest.last_name}"],
            ['Email:', booking.guest.email],
            ['Phone:', booking.guest.phone_number or 'N/A'],
        ]
        
        guest_table = Table(guest_data, colWidths=[1.5*inch, 4*inch])
        guest_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        elements.append(guest_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Booking details
        booking_info = Paragraph("<b>Booking Details:</b>", styles['Heading2'])
        elements.append(booking_info)
        
        booking_data = [
            ['Room:', booking.room.room_number],
            ['Room Type:', booking.room.get_room_type_display()],
            ['Check-in Date:', booking.check_in.strftime('%Y-%m-%d')],
            ['Check-out Date:', booking.check_out.strftime('%Y-%m-%d')],
            ['Number of Nights:', str(booking.number_of_nights)],
        ]
        
        booking_table = Table(booking_data, colWidths=[1.5*inch, 4*inch])
        booking_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        elements.append(booking_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Pricing breakdown
        pricing_info = Paragraph("<b>Pricing:</b>", styles['Heading2'])
        elements.append(pricing_info)
        
        pricing_data = [
            ['Room Rate:', f"₱{booking.room.price_per_night:.2f} per night"],
            ['Number of Nights:', str(booking.number_of_nights)],
            ['Subtotal:', f"₱{booking.room.price_per_night * booking.number_of_nights:.2f}"],
            ['', ''],
            ['<b>Total Amount:</b>', f"<b>₱{booking.total_price:.2f}</b>"],
        ]
        
        pricing_table = Table(pricing_data, colWidths=[2*inch, 3*inch])
        pricing_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 11),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ]))
        elements.append(pricing_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Payment information
        if booking.payments.exists():
            payment = booking.payments.latest('created_at')
            payment_info = Paragraph("<b>Payment Information:</b>", styles['Heading2'])
            elements.append(payment_info)
            
            payment_data = [
                ['Payment Method:', payment.get_payment_method_display()],
                ['Payment Status:', payment.get_status_display()],
                ['Transaction ID:', payment.transaction_id or 'N/A'],
            ]
            
            payment_table = Table(payment_data, colWidths=[2*inch, 3*inch])
            payment_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
            ]))
            elements.append(payment_table)
            elements.append(Spacer(1, 0.2*inch))
        
        # Footer
        footer = Paragraph(
            "<i>Thank you for your booking. This invoice is valid proof of payment.</i>",
            styles['Normal']
        )
        elements.append(footer)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        # Return PDF
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Invoice_{invoice_num}.pdf"'
        return response
    
    except ImportError:
        # Fallback: return HTML invoice
        from django.http import HttpResponse
        html_content = f"""
        <html>
        <head>
            <title>Invoice {booking.id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
                th {{ background-color: #f4f4f4; }}
                .total {{ font-weight: bold; font-size: 1.2em; }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <h1>BOOKING INVOICE</h1>
            <p><strong>Invoice Number:</strong> INV-{booking.id:05d}</p>
            <p><strong>Invoice Date:</strong> {booking.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Booking ID:</strong> {booking.id}</p>
            <p><strong>Status:</strong> {booking.get_status_display()}</p>
            
            <h2>Guest Information</h2>
            <p><strong>Name:</strong> {booking.guest.first_name} {booking.guest.last_name}</p>
            <p><strong>Email:</strong> {booking.guest.email}</p>
            <p><strong>Phone:</strong> {booking.guest.phone_number or 'N/A'}</p>
            
            <h2>Booking Details</h2>
            <table>
                <tr>
                    <th>Room Number</th>
                    <th>Room Type</th>
                    <th>Check-in</th>
                    <th>Check-out</th>
                    <th>Nights</th>
                </tr>
                <tr>
                    <td>{booking.room.room_number}</td>
                    <td>{booking.room.get_room_type_display()}</td>
                    <td>{booking.check_in.strftime('%Y-%m-%d')}</td>
                    <td>{booking.check_out.strftime('%Y-%m-%d')}</td>
                    <td>{booking.number_of_nights}</td>
                </tr>
            </table>
            
            <h2>Pricing</h2>
            <table>
                <tr>
                    <td>Room Rate (per night)</td>
                    <td>₱{booking.room.price_per_night:.2f}</td>
                </tr>
                <tr>
                    <td>Number of Nights</td>
                    <td>{booking.number_of_nights}</td>
                </tr>
                <tr>
                    <td>Subtotal</td>
                    <td>₱{booking.room.price_per_night * booking.number_of_nights:.2f}</td>
                </tr>
                <tr class="total">
                    <td>TOTAL AMOUNT</td>
                    <td>₱{booking.total_price:.2f}</td>
                </tr>
            </table>
            
            <div class="footer">
                <p>Thank you for your booking. This invoice is valid proof of payment.</p>
                <p>Generated on {booking.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </body>
        </html>
        """
        return HttpResponse(html_content, content_type='text/html')


# ==================== GUEST COMPLAINT & REFUND VIEWS ====================

@login_required(login_url='auth:login')
@guest_required
def guest_submit_complaint_view(request, booking_id=None):
    """Guest submits a complaint, optionally linked to one of their bookings."""
    selected_booking = None
    if booking_id:
        selected_booking = get_object_or_404(Booking, id=booking_id, guest=request.user)

    guest_bookings = (
        Booking.objects
        .filter(guest=request.user)
        .select_related('room')
        .order_by('-created_at')
    )

    if request.method == 'POST':
        subject = (request.POST.get('subject') or '').strip()
        description = (request.POST.get('description') or '').strip()
        posted_booking_id = request.POST.get('booking')

        if posted_booking_id:
            selected_booking = get_object_or_404(Booking, id=posted_booking_id, guest=request.user)

        if not subject or not description:
            messages.error(request, 'Subject and description are required.')
        else:
            Complaint.objects.create(
                guest=request.user,
                booking=selected_booking,
                subject=subject,
                description=description,
                status=ComplaintStatus.PENDING,
            )
            messages.success(request, 'Your complaint has been submitted successfully.')
            return redirect('bookings:my_complaints')

    context = {
        'booking': selected_booking,
        'guest_bookings': guest_bookings,
    }

    return render(request, 'bookings/submit_complaint.html', context)


@login_required(login_url='auth:login')
@guest_required
def guest_my_complaints_view(request):
    """View all complaints submitted by guest."""
    complaints = Complaint.objects.filter(
        guest=request.user
    ).select_related('booking__room').order_by('-created_at')

    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        complaints = complaints.filter(status=status_filter)

    context = {
        'complaints': complaints,
        'status_filter': status_filter,
        'statuses': ComplaintStatus.choices,
    }

    return render(request, 'bookings/my_complaints.html', context)


@login_required(login_url='auth:login')
@guest_required
def guest_complaint_detail_view(request, complaint_id):
    """View detail of a specific guest complaint."""
    complaint = get_object_or_404(
        Complaint.objects.select_related('booking__room'),
        id=complaint_id,
        guest=request.user
    )

    context = {
        'complaint': complaint,
        'booking': complaint.booking,
    }

    return render(request, 'bookings/complaint_detail.html', context)


@login_required(login_url='auth:login')
@guest_required
def guest_submit_escalation_view(request, booking_id):
    """Legacy guest escalation flow retained for compatibility."""
    from .utils import log_audit

    booking = get_object_or_404(Booking, id=booking_id, guest=request.user)

    if request.method == 'POST':
        complaint_description = (request.POST.get('complaint_description') or '').strip()

        if not complaint_description:
            messages.error(request, 'Complaint description is required.')
            return redirect('bookings:booking_detail', booking_id=booking_id)

        complaint = GuestComplaintEscalation.objects.create(
            booking=booking,
            guest=request.user,
            complaint_description=complaint_description,
            status='OPEN'
        )

        log_audit(
            request,
            request.user,
            'COMPLAINT_SUBMITTED',
            'GuestComplaintEscalation',
            complaint.id,
            description=f'Guest submitted complaint for Booking {booking.id}',
            changes={'status': 'OPEN'}
        )

        messages.success(request, 'Your complaint has been submitted. Our management team will review it shortly.')
        return redirect('bookings:booking_detail', booking_id=booking_id)

    context = {
        'booking': booking,
    }

    return render(request, 'bookings/submit_complaint.html', context)


@login_required(login_url='auth:login')
@guest_required
def guest_request_refund_view(request, booking_id):
    """Guest requests a refund for their booking"""
    from decimal import Decimal
    from .models import RefundRequest, RefundRequestStatus, Payment, PaymentStatus
    from .utils import log_audit
    
    booking = get_object_or_404(Booking, id=booking_id, guest=request.user)
    
    # Resolve payment safely even if historical duplicates exist.
    payment = (
        Payment.objects
        .filter(booking=booking, status=PaymentStatus.COMPLETED)
        .order_by('-completed_at', '-created_at')
        .first()
    )
    if payment is None:
        messages.error(request, 'Refund requests are only available after a payment has been completed.')
        return redirect('bookings:booking_detail', booking_id=booking_id)

    # Prevent duplicate request for same booking (RefundRequest is OneToOne with Booking)
    existing_refund = RefundRequest.objects.filter(booking=booking).first()
    if existing_refund:
        messages.info(
            request,
            f'You already submitted a refund request for this booking (status: {existing_refund.get_status_display()}).'
        )
        return redirect('bookings:refund_detail', refund_id=existing_refund.id)
    
    if request.method == 'POST':
        refund_amount = request.POST.get('refund_amount')
        reason = (request.POST.get('reason') or '').strip()
        
        if not refund_amount or not reason:
            messages.error(request, 'Refund amount and reason are required.')
            return redirect('bookings:booking_detail', booking_id=booking_id)
        
        try:
            refund_amount = Decimal(refund_amount)
            if refund_amount <= 0 or refund_amount > payment.amount:
                messages.error(request, 'Invalid refund amount.')
                return redirect('bookings:booking_detail', booking_id=booking_id)
        except (ValueError, TypeError):
            messages.error(request, 'Invalid refund amount.')
            return redirect('bookings:booking_detail', booking_id=booking_id)
        
        # Create refund request visible to manager refund queue
        try:
            refund_request = RefundRequest.objects.create(
                booking=booking,
                requested_by=request.user,
                status=RefundRequestStatus.REQUESTED,
                reason=reason,
                requested_amount=refund_amount
            )
        except IntegrityError:
            # Handles race condition if duplicate request submitted quickly
            existing_refund = RefundRequest.objects.filter(booking=booking).first()
            if existing_refund:
                messages.info(
                    request,
                    f'You already submitted a refund request for this booking (status: {existing_refund.get_status_display()}).'
                )
                return redirect('bookings:refund_detail', refund_id=existing_refund.id)
            raise
        
        # Log audit
        log_audit(
            request,
            request.user,
            'REFUND_REQUESTED_BY_GUEST',
            'RefundRequest',
            refund_request.id,
            description=f'Guest requested refund of ₱{refund_amount} for Booking {booking.id}',
            changes={'status': 'REQUESTED', 'requested_amount': str(refund_amount)}
        )
        
        messages.success(request, 'Your refund request has been submitted. Our management team will review it shortly.')
        return redirect('bookings:booking_detail', booking_id=booking_id)
    
    context = {
        'booking': booking,
        'payment': payment,
    }
    
    return render(request, 'bookings/request_refund.html', context)


@login_required(login_url='auth:login')
@guest_required
def guest_my_refund_requests_view(request):
    """View all refund requests submitted by guest"""
    from .models import RefundRequest
    
    refunds = RefundRequest.objects.filter(
        requested_by=request.user
    ).select_related('booking', 'approved_by').order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status', 'all')
    if status_filter == RefundRequestStatus.APPROVED:
        status_filter = 'all'
    if status_filter != 'all':
        refunds = refunds.filter(status=status_filter)

    visible_statuses = [
        choice for choice in RefundRequestStatus.choices
        if choice[0] != RefundRequestStatus.APPROVED
    ]
    
    context = {
        'refunds': refunds,
        'status_filter': status_filter,
        'statuses': visible_statuses,
    }
    
    return render(request, 'bookings/my_refunds.html', context)


@login_required(login_url='auth:login')
@guest_required
def guest_refund_detail_view(request, refund_id):
    """View detail of a specific refund request"""
    from .models import RefundRequest
    
    refund = get_object_or_404(
        RefundRequest,
        id=refund_id,
        requested_by=request.user
    )
    
    context = {
        'refund': refund,
        'booking': refund.booking,
    }
    
    return render(request, 'bookings/refund_detail.html', context)
