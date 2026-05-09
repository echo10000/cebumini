# 🚀 Guest Messaging Quick Reference

## ✨ NEW: Auto-Update Feature

Your messages and replies now **update automatically** while you're viewing them!

### What Changed?
- ✅ **No more manual refresh** needed
- ✅ **See new replies in real-time** (every 5 seconds)
- ✅ **Notifications appear** when new replies are added
- ✅ **Auto-scrolls** to show latest replies

### How It Works (Step by Step)

```
1. You open a message modal
         ↓
2. System fetches message + all replies
         ↓
3. Auto-polling STARTS (checks every 5 seconds)
         ↓
4. If another staff member replies while modal is open:
   - ✨ New reply appears automatically
   - 🔔 Toast notification shows
   - ↗️ Auto-scrolls to new reply
         ↓
5. You close modal
         ↓
6. Auto-polling STOPS (saves bandwidth)
```

---

## 💬 How Guests Contact You

### Where Do Guest Messages Come From?
1. **Contact Form** at `/auth/contact/`
2. **Homepage** "Get In Touch" section
3. Both save to same place: **Guest Services**

### Message Contains
- Guest name & email
- Phone number (optional)
- Subject line
- Full message text
- Timestamp

---

## 👀 Viewing Guest Messages

### Access Guest Services
- **URL**: `/staff/guest-services/`
- **Location**: Staff Dashboard → Guest Services

### What You See
- **Stats**: Total / Unread / Pending / Replied counts
- **Search**: Find messages by guest name, email, or subject
- **Table**: All messages with status badges

### Status Meanings
- 🟡 **Pending**: Viewed but no reply sent yet
- 🟢 **Replied**: Staff has already responded
- 📬 **Unread**: New message not yet opened

---

## 📬 Sending a Reply

### Step-by-Step
1. Click **"View"** button on any message
2. Modal opens with full conversation
3. Scroll to reply area at bottom
4. Type your response in the text box
5. Click **"Send Reply & Email Guest"**
6. ✅ Done! Guest receives email + reply saved

### What Happens Automatically
- ✅ Reply saved to database
- ✅ Email sent to guest immediately
- ✅ Modal updates instantly
- ✅ Table status changes to "Replied"
- ✅ Toast notification confirms success

---

## 🤝 Team Collaboration

### All Staff See All Messages
- ✅ You see every guest message
- ✅ Your team sees your replies
- ✅ Avoid duplicate responses
- ✅ Easy handoffs if needed

### Multiple Replies Allowed
- 1️⃣ First staff member replies
- 2️⃣ Guest gets first response
- 3️⃣ Second staff member can add to conversation
- 4️⃣ Full discussion thread visible to all

---

## 🔍 Finding Messages Quickly

### Search/Filter
1. Type in search box: **"By guest name, email, or subject"**
2. Results filter in real-time
3. No submit button needed

### Reset Search
- Click **"Reset"** button to clear filters

### Sort
- Messages sorted newest first
- Click "View" on any message

---

## 🔔 Notifications & Toast Messages

### Success (Green)
✅ "Reply sent successfully and email notification sent to guest!"

### Info (Blue)  
ℹ️ "✨ New reply added! Auto-updated"
→ Appears when other staff member replies while you have modal open

### Error (Red)
❌ "Error sending reply. Please check your connection..."
→ Please try again or contact admin

### Warning (Yellow)
⚠️ "Please enter a reply"
→ Reply text cannot be empty

---

## ⏱️ Real-Time Update Timing

### Polling Happens Every 5 Seconds
- Checks if new replies were added
- Doesn't interrupt your work
- Stops when modal closes
- No page reload needed

### What You Might See
```
14:30 - You open message
14:30 - Auto-poll starts
14:35 - Colleague adds reply
14:40 - ✨ NEW REPLY appears automatically
       (notification + scroll)
```

---

## 📱 Browser Compatibility

- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Mobile browsers
- ⚠️ Requires JavaScript enabled

---

## 🆘 Troubleshooting

### Replies Not Appearing?
1. Make sure modal is still **open**
2. Wait up to **5 seconds** for next check
3. If still missing, try **refreshing** page

### Toast Not Showing?
- Check if notifications are **enabled** in browser
- Toast auto-dismisses after **5 seconds**

### Can't Send Reply?
- Check reply box is **not empty**
- Verify **internet connection** active
- Try refreshing page if error persists

### Email Not Sent?
- Contact admin to verify email configuration
- Check guest's email is correct in message
- May take 1-2 minutes to arrive

---

## 💡 Pro Tips

### Tip #1: Quick Scanning
1. Scan all message subjects first
2. Note the unread/pending counts
3. Start with highest priority

### Tip #2: Team Coordination
- Before replying, check if colleague already responded
- Use multiple replies for complex issues
- Reference previous replies in your response

### Tip #3: Email Efficiency
- Guest receives email of **full reply**
- They can reply via email or contact form
- Each interaction creates new entry

### Tip #4: Status Tracking
- Pending = You need to respond
- Replied = Already handled
- Use this to prioritize work

---

## 📊 Sample Workflow

```
Monday 9:00 AM
├─ You log in to Guest Services
├─ See: 10 total | 3 unread | 2 pending
├─ Click "View" on unread message
├─ Modal opens with auto-polling active
│
├─ You type reply: "We have availability..."
├─ Click "Send Reply & Email Guest"
│
├─ ✅ Success toast shows
├─ Modal auto-refreshes with your reply
├─ Table updates: Status now "Replied"
│
├─ Guest receives email in seconds
├─ You click next message
└─ Process repeats...

During your work:
- Colleague adds reply to message you're viewing
- ✨ Notification appears automatically
- New reply visible without any action
```

---

## 🎯 Daily Checklist

- [ ] Check Guest Services each morning
- [ ] Review unread count
- [ ] Respond to pending messages
- [ ] Keep an eye for auto-updates while replying
- [ ] Monitor email for any issues

---

## 📞 Need Help?

If you encounter issues:
1. Check this quick reference guide
2. Try refreshing the browser
3. Clear browser cache if problems persist
4. Contact admin with screenshot of error

---

## ✨ That's It!

The system now does the heavy lifting:
- ✅ Auto-checks for new replies
- ✅ No page refresh needed
- ✅ Instant notifications
- ✅ Seamless collaboration

**Just open a message, wait, and watch new replies appear!** 🎉
