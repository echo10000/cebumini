# 🧵 Guest Messaging System - Complete Guide

## 📋 Overview

The guest messaging system allows guests to send inquiries/messages to staff, and enables staff members to reply. The system now features **auto-update functionality** so messages and replies appear instantly without page refresh.

---

## 👥 How Guests Can Message Staff

### 1️⃣ Contact Form (Public)
Guests can submit messages through the **Contact Page**:
- **URL**: `/auth/contact/` (or link from homepage)
- **Visible to**: Anyone (guests, staff, public)
- **Message stored**: Saved to database as `ContactMessage`

### 2️⃣ Homepage Contact Section
On the homepage (`/`), there's a "Get In Touch" section with a contact form:
- Pre-populated form fields: Name, Email, Phone, Subject, Message
- Same backend as the contact page
- Messages go to the same `ContactMessage` table

### 3️⃣ Message Flow (Guest Side)
```
Guest fills form at /auth/contact/
         ↓
Form submitted (POST)
         ↓
ContactMessage created in database
         ↓
Success message shown
         ↓
Guest redirected to homepage
```

---

## 💼 Staff Receiving & Replying

### Access Guest Services
**URL**: `/staff/guest-services/`
**Requirement**: Staff member or admin account
**Permissions**: `@staff_or_admin_required` decorator

### What Staff See
- **Dashboard Stats**:
  - 📧 Total Inquiries
  - 🔔 Unread Messages
  - ⏳ Pending Reply
  - ✅ Replied

- **Search/Filter**: By guest name, email, or subject

- **Message Table** with columns:
  - Guest name & email
  - Message subject
  - Status (Pending/Replied)
  - View button

---

## 🔄 Auto-Update Feature (NEW)

### How It Works

When a staff member **opens a message modal**:

1. **Immediate Load**: Message details and reply history load via AJAX
2. **Auto-Poll Starts**: System checks for new replies every **5 seconds**
3. **Auto-Display**: Any new replies from other staff are instantly shown
4. **Notification**: A subtle info toast appears: "✨ New reply added! Auto-updated"
5. **Auto-Scroll**: Latest reply scrolls into view automatically
6. **Stops on Close**: Polling stops when modal closes (saves bandwidth)

### Example Timeline
```
14:30 - Staff A opens message modal
14:35 - Auto-polling starts (checks every 5 seconds)
14:38 - Staff B adds a reply while Staff A has modal open
14:40 - AUTO-UPDATE: Staff A sees the new reply instantly ✨
        (no refresh needed!)
14:42 - Staff A closes modal → polling stops
```

---

## 📨 Replying to Messages

### Send Reply
1. Open modal for a message
2. Type reply in text area
3. Click "Send Reply & Email Guest"
4. Reply is created AND email sent to guest automatically

### What Happens
```
Staff sends reply
    ↓
MessageReply created in database
    ↓
ContactMessage.is_replied = True
    ↓
Email sent to guest with full context
    ↓
Modal updates instantly (reply appears)
    ↓
Table status badge changes to "Replied" ✓
```

### Guest Receives Email
Email includes:
- Guest's original message (quoted)
- Staff's reply
- Hotel contact information
- Professional formatting with branding

---

## 🔐 Message Visibility & Permissions

### Who Can See Messages?
✅ **ALL STAFF MEMBERS** can see **ALL guest messages**
✅ **ADMINS** can see all messages
❌ **Guests cannot see** staff messages or responses to others
❌ **Public visitors cannot see** any messages

### Why All Staff Can See All?
This allows:
- Team transparency
- Avoiding duplicate replies
- Collaborative problem-solving
- Seamless handoffs if a staff member is unavailable

### Database Models

#### ContactMessage (Guest's Original Inquiry)
```python
- id
- name           → Guest's name
- email          → Guest's email
- phone          → Optional
- subject        → Inquiry subject
- message        → Full message text
- is_read        → Marked when staff views
- is_replied     → True when at least one reply sent
- created_at     → Timestamp
- guest          → FK to CustomUser (if registered)
```

#### MessageReply (Staff's Responses)
```python
- id
- contact_message    → FK to ContactMessage
- staff_member       → FK to CustomUser (who replied)
- reply_text        → Staff's response
- created_at        → When reply sent
- updated_at        → Last edited
```

---

## 🛠️ Technical Details

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/staff/guest-services/` | Main page with all messages |
| GET | `/staff/messages/<id>/` | Fetch message + replies (AJAX) |
| POST | `/staff/messages/<id>/reply/` | Send reply (AJAX) |
| POST | `/auth/contact/` | Guest submits message |

### AJAX Response Format

**GET `/staff/messages/<id>/`**
```json
{
  "success": true,
  "message": {
    "id": 1,
    "name": "Sarah Johnson",
    "email": "sarah@example.com",
    "phone": "+63 917 123 4567",
    "subject": "Wedding Venue Inquiry",
    "message": "We are planning a wedding in June...",
    "created_at": "Apr 20, 2026 at 14:30",
    "is_read": true,
    "is_replied": true
  },
  "replies": [
    {
      "id": 1,
      "staff_name": "John Manager",
      "staff_email": "john@cebuhotel.com",
      "reply_text": "Thank you for considering our venue...",
      "created_at": "Apr 20, 2026 at 15:45"
    },
    {
      "id": 2,
      "staff_name": "Maria Sales",
      "staff_email": "maria@cebuhotel.com",
      "reply_text": "We have availability for June 15th...",
      "created_at": "Apr 20, 2026 at 16:10"
    }
  ]
}
```

---

## ⚡ Frontend Features

### Modal Components
- **Message Details**: Sender info, subject, message body
- **Reply History**: All replies in chronological order
- **Reply Form**: Text area + send button
- **Status Indicators**: Unread/Pending/Replied badges

### Real-Time Updates
- ✅ **No page refresh needed**
- ✅ **Instant reply display**
- ✅ **Auto-polling every 5 seconds**
- ✅ **Smooth animations**
- ✅ **Toast notifications** (success/error/info)

### Toast Notifications
- **Success**: "Reply sent successfully and email notification sent to guest!"
- **Error**: "Error sending reply. Please check your connection..."
- **Info**: "✨ New reply added! Auto-updated"
- Auto-dismiss after 5 seconds

---

## 🧪 Testing the System

### Test Guest Messaging
```bash
1. Go to /auth/contact/
2. Fill in form (or use homepage form)
3. Submit message
4. Check staff Guest Services page
5. Message should appear in table
```

### Test Auto-Update Feature
```bash
1. Open /staff/guest-services/ in Browser 1
2. Open same URL in Browser 2 (Staff Member B)
3. In Browser 1: Click "View" on a message
4. In Browser 2: Click "View" on same message
5. In Browser 2: Type a reply and submit
6. In Browser 1: Wait 5 seconds
7. Result: Reply appears automatically ✨
```

### Test Email Notifications
```bash
1. Guest sends message from /auth/contact/
2. Staff replies in Guest Services
3. Guest checks their email
4. Email received with full context ✓
```

---

## 📊 Performance Considerations

### Polling Interval: 5 Seconds
- **Pros**: Responsive, almost real-time feel
- **Cons**: More API calls

### To Adjust Polling
Edit `templates/staff/guest_services.html`:
```javascript
// Line ~870: Change from 5000 to desired milliseconds
autoUpdateInterval = setInterval(() => {
    fetchAndUpdateMessageDetails(messageId);
}, 5000);  // ← Change this number
```

- 3000 = Every 3 seconds (more responsive)
- 10000 = Every 10 seconds (fewer API calls)
- 30000 = Every 30 seconds (minimal impact)

---

## 🚀 How to Deploy

1. **Database**: Models already in migration
2. **Frontend**: Updated HTML with auto-polling
3. **Backend**: Views already support auto-update
4. **Email**: Configured via `settings.py`

No additional setup needed! System is ready to use.

---

## 📝 Summary

| Feature | Status | Details |
|---------|--------|---------|
| Guest Messaging | ✅ Live | Contact form on `/auth/contact/` |
| Staff Viewing | ✅ Live | All staff see all messages |
| Staff Replying | ✅ Live | Auto-sends email to guest |
| Auto-Update Modal | ✅ NEW | Polls every 5 seconds |
| Real-time Display | ✅ NEW | No page refresh needed |
| Email Notifications | ✅ Live | Guest receives reply via email |
| Search/Filter | ✅ Live | Filter by name/email/subject |
| Status Tracking | ✅ Live | Unread/Pending/Replied badges |

---

## 🆘 Troubleshooting

### Replies Not Appearing?
- Check modal is still open (polling stops when closed)
- Wait 5 seconds for next poll cycle
- Check browser console for errors (F12)

### Email Not Sent?
- Check email configuration in `settings.py`
- Verify Gmail account credentials
- Check "Less secure apps" setting in Gmail

### Polling Too Aggressive?
- Increase polling interval (see Performance section)
- Or disable auto-polling and refresh manually

---

## 📞 Support

For issues or questions:
- Check the database for `ContactMessage` and `MessageReply` records
- Review server logs for AJAX errors
- Verify staff member has `is_staff=True` in database
