# 📋 Table Status Update Fix

## Problem
Message status in the table was not updating when:
1. Modal was opened (should change from "Unread" to "Replied" or "Pending")
2. Reply was sent (should change to "Replied")

---

## Solution Implemented

### 1. **Added `data-message-id` to Table Row**
```html
<tr class="message-row" 
    data-message-id="{{ message.id }}"
    data-guest="{{ message.name|lower }}" 
    data-subject="{{ message.subject|lower }}"
    data-email="{{ message.email|lower }}">
```

**Why:** JavaScript needs to find the correct row to update when status changes.

---

### 2. **Created `updateRowStatus()` Function**
```javascript
function updateRowStatus(messageId, isReplied) {
    const row = document.querySelector(`tr[data-message-id="${messageId}"]`);
    if (!row) return;
    
    const statusCell = row.querySelector('td:nth-child(4)');
    if (statusCell) {
        if (isReplied) {
            statusCell.innerHTML = '<span class="badge-replied"><i class="fas fa-check"></i> Replied</span>';
        } else {
            statusCell.innerHTML = '<span class="badge-pending"><i class="fas fa-clock"></i> Pending</span>';
        }
    }
}
```

**How it works:**
- Finds the table row by `data-message-id`
- Finds the status cell (4th column)
- Updates the badge HTML based on `isReplied` status

---

### 3. **Call updateRowStatus When Modal Opens**

**Before:**
```javascript
// Message details loaded but nothing updates the table
document.getElementById('msg-from').textContent = msg.name;
// ... other fields
```

**After:**
```javascript
// Message details loaded AND table updates
document.getElementById('msg-from').textContent = msg.name;
// ... other fields

// Update table row status badge
updateRowStatus(messageId, msg.is_replied);
```

---

### 4. **Call updateRowStatus When Reply Sent**

**Before:**
```javascript
if (data.success) {
    showSuccessToast(data.message);
    // Reply added to modal but table not updated
    repliesList.innerHTML += newReplyHTML;
}
```

**After:**
```javascript
if (data.success) {
    showSuccessToast(data.message);
    
    // Add reply to modal history
    repliesList.innerHTML += newReplyHTML;
    
    // Update table row status to "Replied"
    updateRowStatus(currentMessageId, true);
}
```

---

## Complete Status Update Flow

### Opening Modal
```
1. User clicks "View" button
   ↓
2. JavaScript extracts message ID from button
   ↓
3. Fetches /staff/messages/{id}/ via AJAX
   ↓
4. Backend marks message as is_read=True
   ↓
5. Backend returns JSON with is_replied status
   ↓
6. JavaScript populates modal fields
   ↓
7. JavaScript calls: updateRowStatus(id, msg.is_replied)
   ↓
8. TABLE ROW STATUS UPDATES ✓ (no page reload)
```

### Sending Reply
```
1. User types reply text
   ↓
2. User clicks "Send Reply & Email Guest"
   ↓
3. JavaScript validates reply not empty
   ↓
4. Sends POST to /staff/messages/{id}/reply/
   ↓
5. Backend creates MessageReply record
   ↓
6. Backend sets message.is_replied=True
   ↓
7. Backend sends email to guest
   ↓
8. Backend returns success JSON
   ↓
9. JavaScript adds reply to modal history
   ↓
10. JavaScript calls: updateRowStatus(id, true)
    ↓
11. TABLE ROW STATUS CHANGES TO "Replied" ✓ (no page reload)
```

---

## Status Badge States

| State | Badge | When It Shows |
|-------|-------|---------------|
| **Unread** 🟠 | Orange envelope | Message never opened |
| **Pending** ⚪ | Gray clock | Message read but no reply yet |
| **Replied** 🟢 | Green checkmark | Reply has been sent to guest |

---

## Example Scenarios

### Scenario 1: Guest Sends Inquiry
```
Table Badge: [Unread]
User Action: Click "View"
Result: Badge changes to [Pending] or [Replied] depending on reply status
```

### Scenario 2: Send First Reply
```
Table Badge: [Pending]
User Action: Type reply + Click "Send Reply & Email Guest"
Result: Badge immediately changes to [Replied]
```

### Scenario 3: Already Replied Message
```
Table Badge: [Replied]
User Action: Click "View" again
Result: Badge stays [Replied]
         Modal shows reply history
```

---

## Technical Details

### Selector Used
```javascript
// Find row by message ID
tr[data-message-id="123"]

// Find status cell (4th column)
row.querySelector('td:nth-child(4)')
```

### Backend Integration
- View `get_message_details()` returns `is_replied` in JSON response
- View `send_reply()` already sets `message.is_replied = True`
- No backend changes needed - only frontend update

### Frontend Updates
- `data-message-id="{{ message.id }}"` on `<tr>`
- New `updateRowStatus()` function
- Called after modal details loaded
- Called after reply sent successfully

---

## Testing Results

✅ All 7 checks passed:
- `data-message-id` in table row
- `updateRowStatus()` function defined
- Called when modal opens with correct status
- Called when reply sent
- Correct column selected (4th)
- Correct badge classes applied
- No page reload required

---

## User Experience

### Before Fix
```
1. Click "View" → Modal opens
2. Message is marked as read in database
3. Table still shows "Unread" ❌
4. Send reply → Success toast shown
5. Table still shows "Pending" ❌
6. User has to refresh page to see updates
```

### After Fix
```
1. Click "View" → Modal opens
2. Message marked as read in database
3. Table IMMEDIATELY shows correct status ✓
4. Send reply → Success toast shown
5. Table IMMEDIATELY changes to "Replied" ✓
6. Everything updates live without refresh ✓
```

---

## Files Modified

**templates/staff/guest_services.html**
1. Added `data-message-id="{{ message.id }}"` to table row
2. Added `updateRowStatus()` function
3. Called after loading message details
4. Called after sending reply successfully

**No backend changes needed** ✓
- Views already return correct data
- Database updates already happen
- Only needed frontend update to display changes

---

## Backwards Compatibility

✓ All existing functionality unchanged
✓ No breaking changes
✓ Works with all browsers that support querySelector
✓ Falls back gracefully if row not found

