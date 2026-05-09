# PayMongo Integration Setup Guide - Cebu Hotel

## 📋 Overview

Your Cebu Hotel system already has **PayMongo integration built-in** for local Philippine payments:
- ✅ **GCash** - Mobile payment solution
- ✅ **Credit/Debit Cards** - Visa & Mastercard
- ✅ **Maya** - Philippine digital wallet

PayMongo is ideal for Philippine-based hotels as it supports local payment methods directly.

---

## 🎯 Step 1: Create PayMongo Account

### 1a. Sign Up
1. Go to https://paymongo.com
2. Click "Sign Up" or "Get Started"
3. Enter your business details:
   - Business Name: Cebu Hotel
   - Business Email: your-email@cebuhotel.com
   - Country: Philippines
   - Business Type: Hotel/Hospitality

### 1b. Verify Your Account
- PayMongo will send a verification email
- Verify your email address
- Complete KYC (Know Your Customer) verification if required
- Add your business bank account for settlements

---

## 🔑 Step 2: Get Your API Keys

### 2a. Find Your Keys
1. Log in to PayMongo Dashboard: https://dashboard.paymongo.com
2. Go to **Developers** → **API Keys**
3. You'll see two key types:
   - **Public Key** (starts with `pk_test_` or `pk_live_`)
   - **Secret Key** (starts with `sk_test_` or `sk_live_`)

### 2b. Identify Test vs Live Keys
**TEST MODE** (for development):
- Public Key: `pk_test_xxxxxxxxxxxxx`
- Secret Key: `sk_test_xxxxxxxxxxxxx`
- Use for testing without real charges

**LIVE MODE** (for production):
- Public Key: `pk_live_xxxxxxxxxxxxx`
- Secret Key: `sk_live_xxxxxxxxxxxxx`
- Real payments will be processed

### 2c. Copy Your Keys
Keep both keys handy for the next step!

---

## ⚙️ Step 3: Configure Environment Variables

### 3a. Create or Update `.env` File

Create a `.env` file in your project root:

```bash
# PayMongo Configuration
PAYMONGO_PUBLIC_KEY=pk_test_xxxxxxxxxxxxx
PAYMONGO_SECRET_KEY=sk_test_xxxxxxxxxxxxx
PAYMONGO_TEST_MODE=True
```

Replace `xxxxxxxxxxxxx` with your actual keys from PayMongo.

### 3b. Update `cebuhotel/settings.py`

The settings are already configured to read from environment variables:

```python
# PayMongo Configuration (in settings.py - already set up)
PAYMONGO_PUBLIC_KEY = os.getenv('PAYMONGO_PUBLIC_KEY', 'pk_test_xyz123456789')
PAYMONGO_SECRET_KEY = os.getenv('PAYMONGO_SECRET_KEY', 'sk_test_xyz123456789')
PAYMONGO_TEST_MODE = True  # Set to False for production
```

**No changes needed** - just ensure your `.env` file has the correct keys!

---

## 📦 Step 4: Verify Dependencies

### 4a. Check `requirements.txt`

Your project already has PayMongo installed:

```
paymongo
stripe
requests
```

### 4b. Verify Installation

Run in your terminal:
```bash
pip install -r requirements.txt
```

Confirm `paymongo` package is installed:
```bash
pip show paymongo
```

---

## 🔗 Step 5: URL Configuration (Already Done)

Your URLs are already configured in `authentication/urls_bookings.py`:

```python
# PayMongo Payment URLs
path('<int:booking_id>/payment/', paymongo_payment_view, name='paymongo_payment'),
path('paymongo-callback/', paymongo_callback, name='paymongo_callback'),
path('webhook/paymongo/', paymongo_webhook, name='paymongo_webhook'),
```

**Accessible at:**
- Payment page: `http://localhost:8000/bookings/{booking_id}/payment/`
- Callback handler: `http://localhost:8000/bookings/paymongo-callback/`
- Webhook endpoint: `http://localhost:8000/bookings/webhook/paymongo/`

---

## 🎨 Step 6: Payment Flow Integration

### Current Flow:
1. Guest creates booking
2. Guest clicks "Pay Now" button
3. Redirected to PayMongo payment page
4. Guest selects payment method (GCash, Card, or Maya)
5. Guest completes payment
6. Return to hotel system with confirmation
7. Booking status updates to CONFIRMED

### Implementation Status:
- ✅ PayMongoHandler class created
- ✅ Checkout session creation
- ✅ Callback handling
- ✅ Webhook support
- ✅ Payment status tracking
- ✅ Templates created

---

## 🧪 Step 7: Testing in Test Mode

### 7a. Test GCash Payment

1. Go to your booking payment page
2. Click "Proceed to Secure Payment"
3. Select **GCash** payment method
4. Use these test credentials:
   ```
   Phone Number: +63917-123-4567 (any format)
   OTP: 123456 (any code)
   ```
5. Confirm payment
6. Should see "Payment Successful" message

### 7b. Test Credit Card

1. On PayMongo checkout page
2. Select **Cards** option
3. Use test card:
   ```
   Card Number: 4242 4242 4242 4242
   Expiry: 12/25 (any future date)
   CVC: 123 (any 3 digits)
   ```
4. Complete payment
5. Check booking status updated to CONFIRMED

### 7c. Test Maya

1. On payment page
2. Select **Maya** option
3. Use test credentials provided by PayMongo
4. Complete payment flow

---

## 🔐 Step 8: Webhook Configuration

### 8a. What is a Webhook?

A webhook notifies your system when a payment is completed, even if the user doesn't return to your site.

### 8b. Set Up in PayMongo Dashboard

1. Log in to PayMongo Dashboard
2. Go to **Developers** → **Webhooks**
3. Click **+ Add Webhook**
4. Configure:
   ```
   Endpoint URL: https://yourdomain.com/bookings/webhook/paymongo/
   Events: Select "charge.updated"
   ```
5. Save the webhook

### 8c. For Local Testing

Use a tool like **ngrok** to expose your local server:

```bash
# Install ngrok (if not already)
# Download from https://ngrok.com/download

# Start ngrok
ngrok http 8000

# You'll get a URL like: https://abc123.ngrok.io
# Use this URL in webhook: https://abc123.ngrok.io/bookings/webhook/paymongo/
```

---

## 📊 Step 9: Monitor Payments

### 9a. View Payment Records

In Django admin:
1. Go to `/admin/`
2. Navigate to **Payments**
3. See all payment attempts:
   - Payment method (PayMongo, Stripe, etc.)
   - Status (PENDING, COMPLETED, FAILED)
   - Transaction ID
   - Amount and currency

### 9b. View in PayMongo Dashboard

1. Log in to PayMongo Dashboard
2. Go to **Transactions**
3. See real-time payment activity
4. View customer details and payment methods used

---

## 🚀 Step 10: Deployment to Production

### 10a. Use Live Keys

When ready to go live:

1. Get your **Live API Keys** from PayMongo Dashboard
2. Update `.env` file:
   ```bash
   PAYMONGO_PUBLIC_KEY=pk_live_xxxxxxxxxxxxx
   PAYMONGO_SECRET_KEY=sk_live_xxxxxxxxxxxxx
   PAYMONGO_TEST_MODE=False
   ```

3. Update webhook URL to your production domain:
   ```
   https://yourdomain.com/bookings/webhook/paymongo/
   ```

### 10b. Security Checklist Before Going Live

- [ ] `.env` file is in `.gitignore` (not committed to Git)
- [ ] Debug mode is `False` in settings
- [ ] HTTPS is enabled on your domain
- [ ] Database is backed up
- [ ] Test a few transactions with small amounts
- [ ] Monitor transaction logs daily

---

## 🐛 Troubleshooting

### Issue: "PayMongo API error: 401"

**Solution:** Check API keys in `.env`:
```bash
# Make sure these are correct
PAYMONGO_PUBLIC_KEY=pk_test_xxxxxxxxxxxxx
PAYMONGO_SECRET_KEY=sk_test_xxxxxxxxxxxxx
```

### Issue: "Invalid signature" on webhook

**Solution:** Webhook signature verification requires:
- Secret key is correct
- Webhook URL matches PayMongo settings
- Request payload is received unmodified

### Issue: Payment completed but booking not confirmed

**Solution:** Check:
1. Webhook is configured in PayMongo Dashboard
2. PayMongo can reach your webhook URL (test with ngrok if local)
3. Django logs for webhook errors:
   ```bash
   tail -f logs/django.log
   ```

### Issue: "No module named 'paymongo'"

**Solution:** Install dependencies:
```bash
pip install -r requirements.txt
python manage.py runserver
```

---

## 📝 Key Files Modified/Created

| File | Purpose |
|------|---------|
| `authentication/views_paymongo.py` | PayMongo handler class & views |
| `authentication/urls_bookings.py` | PayMongo URL routes |
| `templates/payments/paymongo_payment.html` | Payment page UI |
| `authentication/models.py` | Payment & Status models |
| `cebuhotel/settings.py` | Environment variable config |

---

## 💡 Best Practices

1. **Test Thoroughly** - Always test in test mode before going live
2. **Monitor Webhooks** - Set up alerts for failed payments
3. **Keep Keys Secret** - Never commit `.env` to Git
4. **Log Transactions** - Keep records for accounting
5. **Handle Failures** - Implement retry logic for failed payments
6. **Customer Support** - Display clear error messages

---

## 📞 Support

- **PayMongo Support:** https://support.paymongo.com
- **PayMongo Documentation:** https://developers.paymongo.com
- **PayMongo Dashboard:** https://dashboard.paymongo.com

---

## ✅ Verification Checklist

Use this to verify your setup is complete:

- [ ] PayMongo account created and verified
- [ ] API keys obtained (test mode)
- [ ] `.env` file created with correct keys
- [ ] `paymongo` package installed (`pip show paymongo`)
- [ ] URLs configured and accessible
- [ ] Test payment successful in test mode
- [ ] Webhook configured in PayMongo Dashboard
- [ ] Booking status updated after payment
- [ ] Production keys ready (for going live)
- [ ] All transactions logged in Django admin

---

## 🎉 You're Ready!

Your PayMongo integration is ready to:
1. Accept GCash payments from Philippine customers
2. Accept international Visa/Mastercard payments
3. Accept Maya wallet payments
4. Track all transactions in your admin dashboard
5. Automatically confirm bookings after payment

Start accepting payments today!
