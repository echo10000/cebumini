from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator
from datetime import datetime
from decimal import Decimal

from .models import Booking, Room, BookingStatus, Payment, PaymentStatus
from .forms_bookings import (
    BookingForm, BookingFilterForm, BookingConfirmationForm, CancelBookingForm
)
from .views_recommendations import get_recommendations_context
from .decorators import guest_required, admin_required


# ==================== GUEST VIEWS ====================

@login_required(login_url='login')
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
        form = BookingForm(room=room)
    
    # Get available dates (occupied dates for calendar display)
    occupied_dates = []
    bookings = Booking.objects.filter(
        room=room,
        status__in=[BookingStatus.PENDING, BookingStatus.CONFIRMED]
    )
    for booking in bookings:
        current_date = booking.check_in
        while current_date < booking.check_out:
            occupied_dates.append(current_date.isoformat())
            current_date = current_date + timezone.timedelta(days=1)

    context = {
        'form': form,
        'room': room,
        'occupied_dates': occupied_dates,
    }
    return render(request, 'bookings/create_booking.html', context)


@login_required(login_url='login')
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


@login_required(login_url='login')
def booking_detail_view(request, booking_id):
    """View booking details"""
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Check authorization: guest can only view their own bookings
    if request.user != booking.guest and not request.user.is_admin():
        messages.error(request, 'You do not have permission to view this booking.')
        return redirect('rooms:list')
    
    can_cancel = booking.can_be_cancelled()
    
    # Get recommendations for this booking
    recommendations_context = get_recommendations_context(
        request,
        exclude_room_id=booking.room.id,
        limit=3
    )
    
    context = {
        'booking': booking,
        'can_cancel': can_cancel,
        'recommendations': recommendations_context['recommendations'],
        'has_recommendations': recommendations_context['has_recommendations'],
    }
    return render(request, 'bookings/booking_detail.html', context)


@login_required(login_url='login')
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


@login_required(login_url='login')
def cancel_booking_view(request, booking_id):
    """Cancel a booking with refund processing"""
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Check authorization
    if request.user != booking.guest and not request.user.is_admin():
        messages.error(request, 'You do not have permission to cancel this booking.')
        return redirect('rooms:list')
    
    # Check if booking can be cancelled
    if not booking.can_be_cancelled():
        messages.error(request, 'This booking cannot be cancelled.')
        return redirect('bookings:booking_detail', booking_id=booking_id)
    
    if request.method == 'POST':
        cancel_form = CancelBookingForm(request.POST)
        
        if cancel_form.is_valid():
            # Calculate refund amount
            refund_amount, refund_percent, refund_policy = booking.get_refund_amount()
            
            # Get the most recent payment record
            try:
                payment = booking.payments.latest('created_at')
            except:
                payment = None
            
            # Update booking
            booking.status = BookingStatus.CANCELLED
            booking.cancellation_reason = cancel_form.cleaned_data.get('reason', '')
            booking.cancelled_at = timezone.now()
            booking.save()
            
            # Update payment if exists
            if payment and payment.status == PaymentStatus.COMPLETED:
                if refund_amount > 0:
                    payment.refund_amount = refund_amount
                    payment.refund_reason = f'{refund_policy} - Booking cancelled by {request.user.email}'
                    if refund_amount >= payment.amount:
                        payment.status = PaymentStatus.REFUNDED
                    else:
                        payment.status = PaymentStatus.PARTIALLY_REFUNDED
                    payment.refunded_at = timezone.now()
                    payment.save()
                    
                    messages.success(
                        request,
                        f'Booking #{booking.id} cancelled. Refund: PHP {refund_amount:.2f} ({refund_percent}%) - {refund_policy}'
                    )
                else:
                    messages.warning(
                        request,
                        f'Booking #{booking.id} cancelled. No refund available - {refund_policy}'
                    )
            else:
                messages.success(
                    request,
                    f'Booking #{booking.id} has been cancelled successfully.'
                )
            
            return redirect('bookings:booking_history')
    else:
        cancel_form = CancelBookingForm()
    
    # Calculate refund info for display
    refund_amount, refund_percent, refund_policy = booking.get_refund_amount()
    
    context = {
        'booking': booking,
        'cancel_form': cancel_form,
        'refund_amount': refund_amount,
        'refund_percent': refund_percent,
        'refund_policy': refund_policy,
        'cancellation_policy': booking.get_cancellation_policy_display(),
    }
    return render(request, 'bookings/cancel_booking.html', context)


# ==================== ADMIN VIEWS ====================

@login_required(login_url='login')
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


@login_required(login_url='login')
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


@login_required(login_url='login')
def admin_confirm_booking_view(request, booking_id):
    """Admin: confirm a pending booking"""
    if not request.user.is_admin():
        messages.error(request, 'Admin access required.')
        return redirect('rooms:list')
    
    booking = get_object_or_404(Booking, id=booking_id)
    
    if booking.status != BookingStatus.PENDING:
        messages.warning(request, 'This booking is already confirmed or cancelled.')
        return redirect('bookings:admin_bookings')
    
    booking.status = BookingStatus.CONFIRMED
    booking.save()
    
    messages.success(
        request,
        f'Booking #{booking.id} for {booking.guest.username} has been confirmed.'
    )
    return redirect('bookings:admin_bookings')


@login_required(login_url='login')
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
