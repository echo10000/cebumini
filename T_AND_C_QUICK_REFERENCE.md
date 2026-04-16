# T&C Flow - Quick Reference Guide

## 🎯 Quick Summary

### **ANSWER TO YOUR QUESTIONS:**

**Q: When should T&C be accepted - at login or after login?**
> **A: AFTER LOGIN, but entity-specific:**
> - **Guests:** Optional redirect to modal (soft enforcement)
> - **Staff:** Mandatory modal (hard enforcement - can't skip)
> - **Admin:** Mandatory modal (hard enforcement - can't skip)

**Q: Should it be the same for all entities?**
> **A: NO - Different entities, different rules:**
> - **Guests:** Non-intrusive, optional features after acceptance
> - **Staff:** Mandatory, can't access staff portal without it
> - **Admin:** Mandatory, can't access admin panel without it

**Q: How to make T&C more aesthetically pleasing?**
> **A: DONE ✅**
> - Beautiful modal with gradient header
> - Professional content (13 sections, 4,500+ words)
> - Scannable layout with bullet points
> - Mobile-optimized responsive design
> - Smooth animations and modern UI

---

## 🔄 Flow Diagrams

### **GUEST FLOW**
```
┌─────────────────────────────────────────┐
│  User Registration                      │
│  ├─ Email, Name, Password               │
│  ├─ ☑ Accept T&C Checkbox (REQUIRED)   │
│  └─ → Submit                            │
└───────────────┬─────────────────────────┘
                │
                ↓
         ✅ Account Created
                │
                ↓
         ┌──────────────────────┐
         │  User Logs In        │
         │  Email + Password    │
         └──────────┬───────────┘
                │
                ↓
      ┌────────────────────────┐
      │ Check T&C Accepted?    │
      └────────┬───────────────┘
               │
        ┌──────┴─────────┐
        │                │
     YES ↓               ↓ NO
        │        ┌────────────────┐
        │        │ Show T&C Modal │
        │        │ (Beautiful UI) │
        │        └────────┬───────┘
        │                 │
        │         ┌───────┴──────────┐
        │         │                   │
        │      Accept ↓               ↓ Exit
        │         │              Limited Features
        │         │              in Dashboard
        │         │
        │         ├─ Accept T&C
        │         ├─ Record timestamp
        │         └─ Set accepted = True
        │                 │
        └────────┬────────┘
                 │
                 ↓
       ✅ Dashboard Access
           (Full Features)
```

---

### **STAFF FLOW**
```
┌─────────────────────────────────────────┐
│  Admin Creates Staff Account            │
│  ├─ Email, Name, Password               │
│  ├─ Role = STAFF                        │
│  └─ → Save                              │
└───────────────┬─────────────────────────┘
                │
                ↓
         Staff Account Created
                │
                ↓
         ┌──────────────────────┐
         │  Staff Logs In       │
         │  Email + Password    │
         └──────────┬───────────┘
                │
                ↓
      ┌────────────────────────┐
      │ Check Role = STAFF     │
      │ + T&C Accepted?        │
      └────────┬───────────────┘
               │
        ┌──────┴──────────┐
        │                 │
        NO T&C            Already Accepted
        ↓                 ↓
   ┌────────────────┐  ✅ Staff Portal
   │ Show T&C Modal │  (Full Access)
   │ Message:       │
   │ "As a Staff    │
   │ member..."     │
   └────────┬───────┘
        (MANDATORY)
            │
     ┌──────┴──────────┐
     │                └─→ ❌ Exit
  Accept ↓                 (Home Page)
     │              (NO staff portal access)
     ├─ Accept T&C
     ├─ Record timestamp
     ├─ Set accepted = True
     └─ Verify role = STAFF
            │
            ↓
       ✅ Staff Portal
         (Full Access)
```

---

### **ADMIN FLOW**
```
┌─────────────────────────────────────────┐
│  Super Admin Creates Admin Account      │
│  ├─ Email, Name, Password               │
│  ├─ Role = ADMIN                        │
│  └─ → Save                              │
└───────────────┬─────────────────────────┘
                │
                ↓
         Admin Account Created
                │
                ↓
         ┌──────────────────────┐
         │  Admin Logs In       │
         │  Email + Password    │
         └──────────┬───────────┘
                │
                ↓
      ┌────────────────────────┐
      │ Check Role = ADMIN     │
      │ + T&C Accepted?        │
      └────────┬───────────────┘
               │
        ┌──────┴──────────┐
        │                 │
        NO T&C            Already Accepted
        ↓                 ↓
   ┌────────────────┐  ✅ Admin Panel
   │ Show T&C Modal │  (Full Access)
   │ Message:       │
   │ "As an         │
   │ Administrator..│
   └────────┬───────┘
        (MANDATORY)
            │
     ┌──────┴──────────┐
     │                 └─→ ❌ Exit
  Accept ↓                 (Home Page)
     │              (NO admin panel access)
     ├─ Accept T&C
     ├─ Record timestamp
     ├─ Set accepted = True
     ├─ Verify role = ADMIN
     └─ Verify all decorators
            │
            ↓
       ✅ Admin Panel
         (Full Access)
```

---

## 📋 Comparison Table

| Feature | Guest | Staff | Admin |
|---------|-------|-------|-------|
| **When Accept?** | Signup + Post-Login | Post-Login | Post-Login |
| **Is Mandatory?** | ❌ Optional* | ✅ **YES** | ✅ **YES** |
| **Can Skip?** | ✅ Yes | ❌ No | ❌ No |
| **Message** | "Please review..." | "As a Staff member..." | "As an Administrator..." |
| **If Declined** | Limited features | No portal access | No admin access |
| **UI Style** | Beautiful modal | Same modal | Same modal |
| **Enforcement** | view check | Decorator check | Decorator check |

*Limited features if not accepted

---

## 🎨 Modal Design

### **Header**
```
┌─────────────────────────────────────────────┐
│  📋 Terms and Conditions                     │
│  Version: 1.0          ⏱️ ~10 min read      │
└─────────────────────────────────────────────┘
```

### **Content Area** (Scrollable)
```
📌 [Role-specific message here]

1. INTRODUCTION & ACCEPTANCE
   - Clear statement of terms...

2. USER ACCOUNT RESPONSIBILITIES
   - Account types and obligations...

... [more sections] ...

13. CONTACT INFORMATION
    - Cebu Hotel Management
    - Email: support@cebuhotel.com
    - Phone: +63 (32) 123-4567
```

### **Footer** (Action Area)
```
┌──────────────────────────────────────────┐
│  ☑ I have read and agree to Terms       │
│                                          │
│  [Exit Btn]     [✓ Accept & Continue]  │
│  (disables     (enables when
│   content      checkbox checked)
│   reading)                              │
└──────────────────────────────────────────┘
```

---

## 🔐 Permission Matrix

### **Who Can Access What (Without T&C)?**

```
┌─────────────────────┬────────┬────────┬────────┐
│ Feature             │ Guest  │ Staff  │ Admin  │
├─────────────────────┼────────┼────────┼────────┤
│ Login               │ ✅     │ ✅     │ ✅     │
│ Dashboard           │ ✅*    │ ❌     │ ❌     │
│ Staff Portal        │ ❌     │ ❌     │ ❌     │
│ Admin Panel         │ ❌     │ ❌     │ ❌     │
│ Book Room           │ ✅*    │ N/A    │ N/A    │
│ View Bookings       │ ✅*    │ ✅*    │ ✅*    │
│ Manage Users        │ ❌     │ ❌     │ ❌     │
│ Financial Reports   │ ❌     │ ❌     │ ❌     │
└─────────────────────┴────────┴────────┴────────┘

✅ = Full Access      ✅* = Limited Access
❌ = No Access        N/A = Not Applicable
```

---

## 🛠️ Technical Details

### **Database Fields**
```python
# User Model
user.terms_accepted          # Boolean: True/False
user.terms_accepted_at       # DateTime: When accepted
user.terms_version           # String: "1.0", "2.0", etc.
user.role                    # Choice: GUEST/STAFF/ADMIN
```

### **Key Views**
```python
✅ login_view()           → Checks T&C, redirects if needed
✅ accept_terms_view()    → Shows modal, processes acceptance
✅ dashboard_view()       → Blocks if T&C not accepted
```

### **Key Decorators**
```python
✅ @admin_required        → Checks admin role + T&C
✅ @staff_or_admin_required → Checks staff/admin role + T&C
✅ @staff_required        → Checks staff role + T&C
```

---

## ✨ What Makes It Better

### **vs. Old Implementation**
```
OLD                                  NEW
────────────────────────────────────────────────
Minimal T&C content      →   Professional 4,500+ words
Separate form page       →   Beautiful modal UI
Same for all users       →   Entity-specific flows
Basic styling            →   Modern gradient design
Limited mobile support   →   Fully responsive
No role differentiation  →   Decorator enforcement
```

### **Professional Features**
- ✅ Gradient header with icons
- ✅ Smooth slide-in animation
- ✅ Custom scrollbar styling
- ✅ Touch-friendly sizes
- ✅ Clear visual hierarchy
- ✅ Keyboard navigation
- ✅ Read time indicator
- ✅ Role-specific messaging

---

## 📱 Mobile View

```
┌─ Smart Phone ─────────────────────┐
│ ┌────────────────────────────────┐│
││ 📋 Terms and Conditions          ││
││ Version: 1.0   ⏱️ ~10 min read   ││
│├────────────────────────────────┤│
││ 📌 Please review T&C carefully..││
││                                  ││
││ [Scrollable content]             ││
││                                  ││
│├────────────────────────────────┤│
││ ☑ I have read and agree...      ││
││                                  ││
││ ┌──────────────────────────────┐││
│││ Exit Without Accepting         │││
││└──────────────────────────────┘││
││ ┌──────────────────────────────┐││
│││ ✓ Accept and Continue          │││
││└──────────────────────────────┘││
│└────────────────────────────────┘│
└───────────────────────────────────┘
```

---

## 🚀 Implementation Status

| Component | Status | Details |
|-----------|--------|---------|
| T&C Content | ✅ Done | 13 sections, professional |
| Modal UI | ✅ Done | Beautiful design, responsive |
| Guest Flow | ✅ Done | Optional redirect |
| Staff Flow | ✅ Done | Mandatory enforcement |
| Admin Flow | ✅ Done | Mandatory enforcement |
| Decorators | ✅ Done | T&C checks integrated |
| Testing | ⏳ Pending | Ready for QA |
| Deployment | ⏳ Pending | Ready for production |

---

## 📞 Testing Quick Links

**Test URLs:**
- Login: `http://localhost:8000/auth/login/`
- Accept T&C: `http://localhost:8000/auth/accept-terms/`
- Dashboard: `http://localhost:8000/auth/dashboard/`
- Admin: `http://localhost:8000/admin/`
- Staff Portal: `http://localhost:8000/staff/`

**Test Accounts:**
1. Guest: Create new account
2. Staff: Create via admin with role=STAFF
3. Admin: Create via admin with role=ADMIN

---

**Last Updated:** February 2, 2026  
**Status:** ✅ READY FOR TESTING
