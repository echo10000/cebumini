# Payment System Testing Guide

## Overview
The Cebu Hotel booking system now includes integrated payment processing with **Stripe** and **GCash** payment methods. Both are configured in **TEST MODE** for free testing.

---

## 🧪 Test Mode Configuration

### Current Settings
- **PAYMENT_TEST_MODE** = `True` (No real charges)
- **STRIPE_PUBLIC_KEY** = `pk_test_51234567890` (Test key)
- **STRIPE_SECRET_KEY** = `sk_test_01234567890` (Test key)
- **GCASH_TEST_MODE** = `True` (Test mode enabled)
- **PAYMENT_CURRENCY** = `PHP` (Philippine Peso)

### Location
See `cebuhotel/settings.py` lines 110-127 for payment configuration.

---

## 💳 Stripe Payment Testing

### What Happens
- User selects "Credit/Debit Card (Stripe)" at payment method selection
- Form captures card details in test mode
- System simulates card validation and payment processing
- **No real charges occur**

### Test Card Numbers

| Card Number | Result | Purpose |
|-------------|--------|---------|
| `4242 4242 4242 4242` | ✅ Success | Default success test card |
| `4000 0000 0000 0002` | ❌ Declined | Simulate payment failure |
| Any other valid format | ✅ Success | Also processes as successful |

### How to Test Stripe

1. **Create a Booking:**
   - Go to Rooms page
   - Select a room
   - Choose check-in and check-out dates
   - Click "Create Booking"
   - Fill in any special requests
   - Click "Confirm Booking"

2. **Select Payment Method:**
   - Choose "Credit/Debit Card (Stripe)"
   - Click "Continue to Payment"

3. **Enter Test Card Details:**
   ```
   Cardholder Name: Test User
   Card Number: 4242 4242 4242 4242
   Expiry Date: 12/25 (any future date)
   CVC: 123 (any 3 digits)
   ```

4. **Click "Pay ₱[amount]":**
   - For success card (4242...): Booking confirmed immediately
   - For failure card (4000...): Payment failed, option to retry

5. **Verification:**
   - ✅ Success: Redirected to payment success page
   - ✅ Booking status changes from PENDING to CONFIRMED
   - ✅ Confirmation details displayed with transaction ID

### Test Scenarios

**Scenario 1: Successful Payment**
```
Card: 4242 4242 4242 4242
Expected: Booking confirmed, email notification
Status in Database: CONFIRMED
Payment Status: COMPLETED
```

**Scenario 2: Failed Payment**
```
Card: 4000 0000 0000 0002
Expected: Payment failed message, retry option
Status in Database: PENDING
Payment Status: FAILED
```

**Scenario 3: Generic Test Card**
```
Card: Any other 16-digit card
Expected: Processes successfully like 4242 card
Status in Database: CONFIRMED
Payment Status: COMPLETED
```

---

## 📱 GCash Payment Testing

### What Happens
- User selects "GCash (Philippine Payment)" at payment method selection
- Form asks for GCash reference number and phone
- System verifies reference format (in test mode)
- **No real GCash transaction occurs**

### How to Test GCash

1. **Create a Booking:**
   - Follow same steps as Stripe (rooms → select dates → confirm)

2. **Select Payment Method:**
   - Choose "GCash (Philippine Payment)"
   - Click "Continue to Payment"

3. **Enter Test Details:**
   ```
   Your GCash Phone Number: +639xxxxxxxxxx
   GCash Reference Number: GCASH-TEST12345678
   ```

4. **Click "Confirm GCash Payment":**
   - Reference must start with "GCASH-" prefix
   - System verifies and processes

5. **Verification:**
   - ✅ Success: Booking confirmed (if reference format valid)
   - ✅ Payment Status: COMPLETED
   - ❌ Failure: Invalid reference format → Payment Failed

### Test Reference Formats

| Format | Result | Notes |
|--------|--------|-------|
| `GCASH-XXXXXXXXXXXX` | ✅ Success | Valid test format |
| `GCASH-TEST123` | ✅ Success | Works in test mode |
| `INVALID-12345` | ❌ Failed | Doesn't start with GCASH- |
| `GCash123456` | ❌ Failed | Wrong case (must be GCASH-) |

### Test Scenarios

**Scenario 1: Successful GCash Payment**
```
Phone: +63917-123-4567 (example)
Reference: GCASH-HELLOWORLD12
Expected: Booking confirmed immediately
Status: CONFIRMED
Payment Status: COMPLETED
```

**Scenario 2: Failed GCash Payment**
```
Phone: +63917-123-4567
Reference: INVALID-REF (doesn't start with GCASH-)
Expected: Payment failed → retry option
Status: PENDING
Payment Status: FAILED
```

---

## 🏦 Bank Transfer Payment Testing

### What Happens
- User selects "Bank Transfer" at payment method selection
- Form captures bank name and reference number
- Payment marked as **PENDING** (waiting for admin verification)
- **No immediate confirmation**

### How to Test Bank Transfer

1. **Create a Booking:**
   - Follow same steps as other methods

2. **Select Payment Method:**
   - Choose "Bank Transfer"
   - Click "Continue to Payment"

3. **Enter Test Details:**
   ```
   Bank Name: BDO
   Reference Number: TRANSFER-TEST12345
   Notes: Testing bank transfer payment method
   ```

4. **Click "Confirm Bank Transfer":**
   - Data saved to database
   - Redirected to "Payment Pending" page

5. **Verification:**
   - Status: PENDING
   - Payment Status: PENDING_VERIFICATION
   - Message: "Pending admin verification"

### Test Scenarios

**Scenario 1: Bank Transfer Submitted**
```
Bank: BPI
Reference: BPI-001234567
Expected: Payment pending page
Status: PENDING
Payment Status: PENDING
Action Required: Admin verification
```

---

## 🔄 Payment Flow Diagram

```
Booking Confirmation
        ↓
   Create Booking (PENDING status)
        ↓
   Select Payment Method
     /    |    \
    /     |     \
Stripe  GCash  Bank Transfer
   |      |        |
   ✓      ✓        ✓
   |      |        |
Success Confirm  Pending
  CONFIRMED  CONFIRMED  PENDING
```

---

## 📊 Testing Checklist

### Stripe Payment Tests
- [ ] Test successful payment (4242 card)
- [ ] Test failed payment (4000 card)
- [ ] Verify booking status changes to CONFIRMED
- [ ] Verify transaction ID is generated
- [ ] Verify success page displays all booking details
- [ ] Test retry after failure
- [ ] Verify email notification sent

### GCash Payment Tests
- [ ] Test successful payment (GCASH- prefix)
- [ ] Test failed payment (invalid reference)
- [ ] Verify booking status changes to CONFIRMED
- [ ] Verify reference number saved
- [ ] Verify success page displays all booking details
- [ ] Test retry after failure
- [ ] Verify email notification sent

### Bank Transfer Tests
- [ ] Test bank transfer submission
- [ ] Verify payment marked as PENDING
- [ ] Verify reference number saved
- [ ] Verify booking stays PENDING until verified
- [ ] Test multiple bank options
- [ ] Verify pending notification page

### General Payment Tests
- [ ] Test payment page URL: `/bookings/<booking_id>/payment/`
- [ ] Test all payment success pages display correctly
- [ ] Test all payment failure pages display correctly
- [ ] Test payment retry functionality
- [ ] Test back button navigation
- [ ] Test booking history shows payment status
- [ ] Test admin dashboard shows payment status

---

## 🔍 Database Verification

### Check Payment Records
```python
# Django shell
python manage.py shell

# View all payments
from authentication.models import Payment
Payment.objects.all()

# Check specific booking's payment
booking_id = 1
from authentication.models import Booking
booking = Booking.objects.get(id=booking_id)
payment = Payment.objects.get(booking=booking)
print(payment.status)
print(payment.payment_method)
print(payment.transaction_id)
```

### Check Booking Status
```python
# Check booking status
booking = Booking.objects.get(id=booking_id)
print(booking.status)  # Should be CONFIRMED if payment successful
```

---

## 🚀 Moving to Production

When ready to go live:

1. **Update Settings:**
   ```python
   # cebuhotel/settings.py
   PAYMENT_TEST_MODE = False  # Changed to False
   STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY')  # Use real key
   STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')  # Use real key
   GCASH_TEST_MODE = False  # Changed to False
   ```

2. **Get Real Keys:**
   - Stripe: https://dashboard.stripe.com/apikeys
   - GCash: Contact GCash Business Solutions

3. **Set Environment Variables:**
   ```
   STRIPE_PUBLIC_KEY=pk_live_...
   STRIPE_SECRET_KEY=sk_live_...
   GCASH_MERCHANT_ID=...
   GCASH_API_KEY=...
   ```

4. **Test Real Payments:**
   - Make small test deposits to verify
   - Monitor transaction logs

---

## 📞 Support & Documentation

### Payment Endpoints
- **Payment Selection:** `/bookings/<booking_id>/payment/`
- **Stripe Form:** `/bookings/<booking_id>/payment/stripe/`
- **GCash Form:** `/bookings/<booking_id>/payment/gcash/`
- **Bank Transfer Form:** `/bookings/<booking_id>/payment/bank-transfer/`
- **Success Page:** `/bookings/<booking_id>/payment/success/`
- **Failed Page:** `/bookings/<booking_id>/payment/failed/`
- **Pending Page:** `/bookings/<booking_id>/payment/pending/`

### Payment Models
- **Payment:** Stores transaction details, amount, status, reference numbers
- **PaymentMethod:** Choices for STRIPE, GCASH, BANK_TRANSFER
- **PaymentStatus:** Choices for PENDING, COMPLETED, FAILED, REFUNDED
- **Booking:** Updated status field to PENDING during payment phase

### Useful Files
- `authentication/forms_payments.py` - Payment forms
- `authentication/views_payments.py` - Payment logic
- `templates/payments/` - Payment templates
- `cebuhotel/settings.py` - Configuration (lines 110-127)

---

## ⚠️ Important Notes

1. **Test Mode Only:**
   - Current system is in FREE TEST MODE
   - No real charges will be made
   - All test transactions are simulated

2. **Booking Status Changes:**
   - Before Payment: PENDING
   - After Successful Payment: CONFIRMED
   - Failed Payment: Booking stays PENDING, can retry

3. **Email Notifications:**
   - Confirmation emails sent after successful payment
   - Configure email in settings for production

4. **Security:**
   - All payment forms use CSRF protection
   - Card details validated before submission
   - Test mode hides sensitive transaction data

5. **Stripe Webhook:**
   - Currently in test mode (verification skipped)
   - Enabled for production webhook handling

---

## 🎯 Next Steps

1. ✅ Test all three payment methods completely
2. ✅ Verify booking status changes as expected
3. ✅ Test error scenarios and recovery
4. ✅ Prepare production credentials when ready
5. ✅ Switch PAYMENT_TEST_MODE to False for live deployment

---

**Created:** $(date)
**System Status:** Development (Test Mode Active)
**Payment Methods:** Stripe + GCash + Bank Transfer
**Test Mode:** Enabled - Free Testing Available
