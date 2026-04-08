# Walk-In Booking with Integrated Payment System

## Overview
The walk-in booking system has been successfully enhanced with integrated payment collection following standard hotel practices. Staff can now create bookings for walk-in guests and collect payment immediately at point of service.

## Features Implemented

### 1. Payment Collection Form
- **Location**: `/staff/manual-booking/`
- **Payment Methods Available**:
  - Cash
  - Card (Credit/Debit via Stripe)
  - GCash (Mobile Payment)
  - Bank Transfer

### 2. Real-time Payment Summary
The form displays a live payment summary that:
- Shows total booking amount due
- Updates as staff enters payment collected
- Calculates remaining balance if partial payment
- Shows payment status (PAID or BALANCE DUE)
- Auto-fills with full amount for convenient processing

### 3. Automatic Payment Recording
When booking is created:
- Payment record automatically linked to booking
- Payment status set to COMPLETED if full payment collected
- Payment status set to PENDING if partial payment only
- Receipt/reference number auto-generated if not provided
- Payment timestamp recorded for audit trail

### 4. Receipt Generation
- Automatic receipt numbers: `RECEIPT-YYYYMMDD-HHMMSS`
- Custom reference numbers supported (e.g., transaction IDs, GCash ref numbers)
- Payment notes stored for internal records

## Standard Hotel Practice Implemented

This system follows standard hotel check-in procedures:

1. **Guest Information Collection**: Name, email, phone number
2. **Room & Dates Selection**: Available rooms with pricing display
3. **Payment Collection**: Full payment required before room access
4. **Automatic Room Blocking**: Room marked unavailable immediately
5. **Guest Account Creation**: Automatic if new email address used
6. **Confirmation**: Booking created with CONFIRMED status

## Payment Flow

### Step-by-Step Process:
1. Staff navigates to Manual Booking form
2. Enters guest information (name, email, phone)
3. Selects available room (system shows price per night)
4. Enters check-in and check-out dates
5. **Form auto-calculates total booking price**
6. Selects payment method
7. Enters amount collected (form auto-suggests full amount)
8. **Optional**: Enters custom receipt/reference number
9. Payment summary shows live calculation with status
10. Clicks "Create Booking" to finalize
11. Payment record created automatically
12. Success message displays booking details with receipt info

## Technical Details

### Database Records Created
- **Booking Record**: 
  - Status: CONFIRMED
  - Contains guest, room, dates, total price
  - Links to Payment record via OneToOne relationship

- **Payment Record**:
  - Amount: Full booking total
  - Payment Method: Selected by staff
  - Status: COMPLETED (if paid) or PENDING (if balance due)
  - Reference Number: Auto-generated or custom
  - Timestamp: When payment was recorded

### Data Validation
- Checks for available rooms
- Validates date ranges (check-out after check-in)
- Auto-creates guest account if email is new
- Updates existing guest info if returning customer
- Marks room as unavailable after booking

### Error Handling
- Room not available: Shows error message
- Missing required fields: Form validation prevents submission
- Booking creation fails: Returns detailed error message
- Payment creation fails: Transaction rolled back

## File Changes

### Modified Files:
1. `authentication/views_staff.py`:
   - Enhanced `manual_booking()` view with payment processing
   - Creates Payment record after booking creation
   - Handles both full and partial payment scenarios

2. `authentication/models.py`:
   - Added CASH to PaymentMethod choices

3. `templates/staff/manual_booking.html`:
   - Added Payment Information section
   - Added Payment Method dropdown
   - Added Amount Collected input field
   - Added Reference Number field
   - Added Payment Summary display table
   - Enhanced JavaScript for real-time calculations
   - Updated instructions and notes

## Usage Examples

### Full Payment Scenario (Most Common)
```
Guest: John Doe (john@example.com)
Room: 101 (Php 150/night)
Dates: Mar 16 - Mar 19 (3 nights)
Total: Php 450
Payment Method: Cash
Amount Collected: Php 450
Status: PAID (Completed)
```

### Partial Payment Scenario
```
Guest: Jane Smith (jane@example.com)
Room: 205 (Php 200/night)
Dates: Mar 16 - Mar 18 (2 nights)
Total: Php 400
Payment Method: Card
Amount Collected: Php 200 (deposit)
Status: BALANCE DUE - Php 200 remaining (Pending)
```

## Testing Verification

Test Case Run Results:
- Room Selection: PASSED (301 available)
- Booking Creation: PASSED (Booking #6 created)
- Payment Record: PASSED (Linked to booking)
- Payment Status: PASSED (Set to COMPLETED)
- Guest Account: PASSED (Auto-created)
- Room Availability: PASSED (Marked unavailable)

## Future Enhancements (Optional)
- SMS notification to guest with receipt
- Email receipt delivery
- Installment payment plans
- POS terminal integration
- Barcode/QR code receipt generation
- Daily settlement reports
- Payment reconciliation tools

## Support Notes
- Supports single or multi-night bookings
- Handles multiple currency display (Php)
- Works with walk-in and phone bookings
- Can process multiple payments per day
- Audit trail maintained for all payments

---
**Implementation Date**: March 16, 2026
**Status**: Production Ready
**Payment Methods**: Cash, Card, GCash, Bank Transfer
