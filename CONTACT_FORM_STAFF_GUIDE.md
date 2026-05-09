# Contact Form - Staff Quick Reference Guide

## Accessing Guest Messages

### Via Django Admin Panel

1. **Login to Admin**
   - URL: `http://127.0.0.1:8000/admin/` (local) or your domain `/admin/`
   - Use staff credentials

2. **Navigate to Contact Messages**
   - Left sidebar → "Contact Messages"
   - You'll see a list of all guest inquiries

3. **View Message Details**
   - Click on any message to open full details
   - See: Name, Email, Phone, Subject, Message, Date, Guest Account (if linked)

### List View Features

| Column | Information |
|--------|-------------|
| **Name** | Guest's full name |
| **Email** | Contact email address |
| **Subject** | Message subject line |
| **Created At** | Date & time submitted |
| **Is Read** | Has staff viewed it? |
| **Is Replied** | Has staff responded? |

### Filtering Messages

**By Status:**
- Click "Is Read" filter: See unread messages
- Click "Is Replied" filter: See unreplied messages

**By Date:**
- Use date range picker
- Sort by "Created At" (newest first = default)

**Search:**
- Search by guest name
- Search by email address
- Search by subject line

### Managing Individual Messages

#### Mark as Read
1. Click message in list
2. Check "Is Read" checkbox
3. Click "Save"

#### Mark as Replied
1. Click message in list
2. Check "Is Replied" checkbox
3. Add internal note if needed (in message area)
4. Click "Save"

## Guest Information

When viewing a message, you'll see:

```
Name:        ________________________
Email:       ________________________
Phone:       ________________________
Subject:     ________________________
Message:     ________________________
Date:        ________________________
Guest:       [Link to guest account if logged in]
Is Read:     ☐
Is Replied:  ☐
```

If guest was logged in when submitting:
- "Guest" field will show their username
- Click to view their profile and booking history

## Communication Workflow

### When You Receive a New Message:

```
1. Guest submits form (homepage or contact page)
   └─ Message saved to database automatically
   
2. Staff opens admin panel
   └─ See message in list (Is Read = unchecked)
   
3. Staff clicks message to read
   └─ View full details and guest info
   
4. Staff marks as "Read"
   └─ Checkbox "Is Read" = checked
   
5. Staff responds via:
   ├─ Email to guest
   ├─ Phone call to guest
   └─ Chatbot escalation (if applicable)
   
6. Staff marks as "Replied"
   └─ Checkbox "Is Replied" = checked
```

## Message Types & Recommended Actions

| Type | How to Identify | Action |
|------|-----------------|--------|
| **Booking Issue** | Keywords: room, dates, confirmation | Check booking system, contact directly |
| **Service Issue** | Keywords: WiFi, AC, water, noise | Create work order, schedule fix |
| **Facility Question** | Keywords: gym, pool, spa, dining | Send info, invite to try |
| **Complaint** | Keywords: wrong room, damaged, late | Apologize, offer compensation |
| **Special Request** | Keywords: birthday, anniversary, dietary | Note request, coordinate with team |
| **General Inquiry** | Website questions, package info | Send brochure, answer question |

## Response Time Goals

- **Urgent** (complaints, issues): Respond within 2 hours
- **Important** (bookings, reservations): Respond within 4 hours
- **General** (information): Respond within 24 hours

## Escalation Path

If message needs special handling:

1. **Housekeeping Issue** → Forward to Housekeeping Manager
2. **Maintenance Issue** → Forward to Engineering/Maintenance
3. **Complaint/Escalation** → Forward to Manager/Admin
4. **Billing Issue** → Forward to Finance
5. **Security Issue** → Alert Security Team immediately

## Dashboard Summary

Quick stats you should monitor:

```
Total Messages:     [number] (all-time)
Unread:             [number] (need attention)
Unreplied:          [number] (need response)
This Week:          [number] (recent activity)
Average Response:   [time] (see quality)
```

## Bulk Actions (if available)

You can select multiple messages to:
- Mark as read
- Mark as replied
- Delete (archive)
- Export to spreadsheet

## Common Responses

### Booking Confirmation
```
Dear [Name],

Thank you for choosing Cebu Hotel! We've received your inquiry about 
[booking dates]. Our reservations team will contact you within 2 hours 
to confirm your booking.

Best regards,
Cebu Hotel Team
```

### Service Issue
```
Dear [Name],

We sincerely apologize for the [issue]. Our maintenance team has been 
notified and will resolve this immediately. Please call [extension] if 
you need urgent assistance.

Thank you for bringing this to our attention.

Best regards,
Cebu Hotel Management
```

### General Information
```
Dear [Name],

Thank you for your inquiry! Here's the information you requested:

[Detailed answer/information]

Please don't hesitate to contact us if you have any other questions.

Best regards,
Cebu Hotel Concierge
```

## Tips for Excellent Service

✅ **Do:**
- Read all messages within business hours
- Respond promptly and professionally
- Use guest's name in response
- Offer solutions, not excuses
- Follow up on complaints
- Thank guests for feedback

❌ **Don't:**
- Leave messages unread for days
- Use generic copy-paste responses
- Ignore complaints or issues
- Make promises you can't keep
- Share guest info publicly

## Troubleshooting

**Can't see a message?**
- Clear browser cache
- Logout and login again
- Check "Is Read" filter isn't hiding it

**Message shows wrong info?**
- Edit the message directly in admin
- Click fields to correct information

**Need to delete a message?**
- Select message checkbox
- Choose "Delete" from dropdown
- Confirm deletion

## Admin Permissions

You need these permissions to:
- **View messages**: Read permission
- **Edit status**: Change permission
- **Delete messages**: Delete permission

Contact admin if you don't have required permissions.

---

**Last Updated**: April 20, 2026  
**Contact System**: Active & Operational ✅
