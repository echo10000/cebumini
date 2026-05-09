# 🚀 PayMongo Quick Start Guide

## ⚡ 5-Minute Setup

### Step 1: Get PayMongo API Keys (2 min)
```
1. Go to https://paymongo.com → Sign Up
2. Create business account (Philippines)
3. Go to Dashboard → Developers → API Keys
4. Copy your TEST keys:
   - Public Key: pk_test_xxxxx
   - Secret Key: sk_test_xxxxx
```

### Step 2: Configure Environment (1 min)
Create `.env` file in project root:
```env
PAYMONGO_PUBLIC_KEY=pk_test_xxxxx
PAYMONGO_SECRET_KEY=sk_test_xxxxx
PAYMONGO_TEST_MODE=True
```

### Step 3: Install Dependencies (1 min)
```bash
pip install -r requirements.txt
```

### Step 4: Test It (1 min)
```bash
# Verify setup
python verify_paymongo_setup.py

# Run full integration test
python test_paymongo_integration.py

# Start server
python manage.py runserver
```

---

## 💳 Test Payment Credentials

### Test GCash
- Phone: Any format (e.g., +63917-123-4567)
- OTP: Any code (e.g., 123456)

### Test Credit Card
- Card: `4242 4242 4242 4242`
- Expiry: `12/25` (any future date)
- CVC: `123` (any 3 digits)

### Test Maya
- Use credentials from PayMongo test panel

---

## 📊 System Overview

```
Guest Books Room
        ↓
Guest Clicks "Pay"
        ↓
Redirected to PayMongo
        ↓
Select: GCash / Card / Maya
        ↓
Complete Payment
        ↓
PayMongo Callback
        ↓
Booking Status → CONFIRMED
```

---

## 🔑 Key Files

| File | Purpose |
|------|---------|
| `.env` | API key configuration |
| `authentication/views_paymongo.py` | Payment processing |
| `templates/payments/paymongo_payment.html` | Payment UI |
| `cebuhotel/settings.py` | Settings (already configured) |

---

## ✅ Verification Checklist

```bash
# 1. Check .env file
ls -la .env

# 2. Test imports
python -c "from paymongo import Paymongo; print('✅ PayMongo installed')"

# 3. Run verification script
python verify_paymongo_setup.py

# 4. Run integration test
python test_paymongo_integration.py

# 5. Start server and test manually
python manage.py runserver
```

---

## 🌐 URLs After Setup

| URL | Purpose |
|-----|---------|
| `/bookings/{id}/payment/` | Payment page |
| `/bookings/paymongo-callback/` | Return from PayMongo |
| `/bookings/webhook/paymongo/` | Webhook endpoint |

---

## 🐛 Immediate Troubleshooting

### "PayMongo API error: 401"
→ Check `.env` - API keys are wrong or not set

### "No module named 'paymongo'"
→ Run: `pip install -r requirements.txt`

### Payment completes but booking not confirmed
→ Webhook not configured - Set up in PayMongo Dashboard

### Can't find PayMongo keys
→ https://dashboard.paymongo.com → Developers → API Keys

---

## 📞 Quick Support Links

- **Dashboard**: https://dashboard.paymongo.com
- **API Docs**: https://developers.paymongo.com
- **Support**: https://support.paymongo.com

---

## 🎯 Next: Going Live

When ready for production:

1. Get **LIVE** API keys from PayMongo Dashboard
2. Update `.env`:
   ```env
   PAYMONGO_PUBLIC_KEY=pk_live_xxxxx
   PAYMONGO_SECRET_KEY=sk_live_xxxxx
   PAYMONGO_TEST_MODE=False
   ```
3. Update webhook URL to your production domain
4. Enable HTTPS on your website
5. Test with small amount
6. Monitor PayMongo Dashboard daily

---

💡 **Tip**: Always test in test mode first before going live!
