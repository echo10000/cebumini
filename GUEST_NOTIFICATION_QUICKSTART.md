# Guest Message Notification System - Quick Reference

## 🎯 What Was Built

A complete notification system ensuring guests know when hotel staff responds to their messages through:
- Email confirmations when message submitted
- Email notifications when staff replies  
- Guest dashboard to view all messages
- In-app notification banner
- Navigation badge with unread count

---

## 📍 Key URLs

| Purpose | URL |
|---------|-----|
| Submit Contact Form | `/auth/contact/` or `/` (homepage) |
| View Messages (Guest) | `/auth/messages/` |
| View Message Detail | `/auth/messages/<id>/` |
| Admin Messages | `/admin/authentication/contactmessage/` |

---

## 🔄 How It Works

### Guest Submits Message
```
Guest fills form → Confirmation email sent → Message saved with guest FK
```

### Guest Checks Status
```
Guest visits /auth/messages/ → Sees all their messages → Can click to view details
```

### Staff Responds
```
Admin clicks "Mark as replied & send notification" → Reply email sent to guest → Banner appears
```

### Guest Gets Notified
```
Notification banner appears → Click to view messages → See full response
```

---

## 📧 Email Templates

### Confirmation Email
- Subject: "We've received your message - [Subject]"
- Includes: Guest name, subject, reference ID, submission time

### Reply Notification Email
- Subject: "[Hotel] Staff Response to Your Message"
- Includes: Staff response text, hotel contact info, message reference

---

## 🛠️ Admin Actions

**Location:** Django Admin > Contact Messages > Actions dropdown

### Action 1: Mark as Read
- Marks selected messages as read
- Updates `is_read = True`

### Action 2: Mark as Replied & Send Email
- Sets `is_replied = True`
- Sends notification email to guest
- Sets `notification_sent = True`
- Records `last_notified_at` timestamp

---

## 📊 Message States

| State | Meaning | Guest Sees |
|-------|---------|-----------|
| Pending | Waiting for staff response | "Awaiting Response" badge |
| Replied & Notified | Staff responded + email sent | "Replied" badge |
| Replied & Not Notified | Staff responded but email not sent | "New Response" warning |

---

## 🎨 UI Components

### Notification Banner (Top of Page)
```
⚠ You have 2 new responses
Staff has replied to your message(s)
[View Messages]
```

### Navigation Badge
```
Envelope icon with red badge showing count: "2"
Link: Messages
```

### Dashboard Card
```
Subject: "Room Inquiry"
Status: "✓ Replied"
Date: "Apr 15, 2026"
Preview: "Thank you for your inquiry..."
```

---

## 📋 Database Fields

```python
ContactMessage model additions:

guest = ForeignKey(CustomUser)           # Guest who submitted
staff_response = TextField()             # Staff's reply message
is_replied = BooleanField()              # Message has been replied to
notification_sent = BooleanField()       # Reply notification email sent
last_notified_at = DateTimeField()       # When guest was last notified
is_read = BooleanField()                 # Guest has read the message
updated_at = DateTimeField(auto_now)     # Last modification time
```

---

## 🚀 Production Deployment

### 1. Configure Email Backend
Choose one:

**SendGrid:**
```python
EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
```

**Gmail:**
```python
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASSWORD')
```

**AWS SES:**
```python
EMAIL_BACKEND = 'django_ses.SESBackend'
AWS_SES_REGION_NAME = 'us-east-1'
```

### 2. Set Environment Variables
```bash
SENDGRID_API_KEY=your_key_here
EMAIL_USER=your_email
EMAIL_PASSWORD=your_password
DEFAULT_FROM_EMAIL=noreply@cebuhotel.com
```

### 3. Test Email Sending
```bash
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Test body', 'noreply@cebuhotel.com', ['test@example.com'])
```

### 4. Deploy
```bash
git add .
git commit -m "Add guest notification system"
git push
```

---

## ✅ Testing

### Quick Test
```bash
python test_guest_notifications.py
```

### Manual Test Checklist
- [ ] Submit form → Check for confirmation email
- [ ] Login as guest → Visit `/auth/messages/`
- [ ] See message listed with status
- [ ] Click message → View details
- [ ] Go to admin → Mark as replied
- [ ] Check guest email for reply notification
- [ ] Return to guest dashboard → See "Replied" status
- [ ] See notification banner appear
- [ ] Check navigation badge shows count

---

## 🔧 Customization

### Change Notification Banner Color
Edit `templates/base.html`:
```html
<!-- Change from fef3c7 (yellow) to desired color -->
<div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);">
```

### Customize Email Content
Edit `authentication/models.py` - `send_confirmation_email()` method:
```python
def send_confirmation_email(self):
    subject = f"Custom Subject - {self.subject}"
    message = f"Custom email body..."
    # ... rest of method
```

### Change Dashboard Layout
Edit `templates/authentication/guest_messages.html`:
- Modify grid columns in CSS
- Change badge colors
- Adjust spacing/fonts

---

## 📞 Support

### Troubleshooting

**Emails not sending:**
1. Check email backend configuration
2. Verify SMTP credentials
3. Check firewall/port access
4. Test with `python manage.py shell`

**Notification banner not showing:**
1. Verify context processor in settings
2. Check user is logged in
3. Verify message has `is_replied=True`

**Guest can't see messages:**
1. Ensure guest is logged in
2. Check message has guest FK set
3. Verify correct URL `/auth/messages/`

---

## 📚 Documentation Files

- `GUEST_NOTIFICATION_SYSTEM_GUIDE.md` - Full technical documentation
- `test_guest_notifications.py` - Complete test suite
- This file - Quick reference guide

---

**Status:** ✅ Production Ready  
**Version:** 1.0  
**Last Updated:** April 20, 2026
