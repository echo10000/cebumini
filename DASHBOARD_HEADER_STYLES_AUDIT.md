# Dashboard Header Styles Audit

## Summary
Found **5 different header styling approaches** across the dashboard and admin pages. These need to be standardized for consistency.

---

## 1. PENDING PAYMENTS - Gold Border Header
**Files:** 
- [templates/admin/pending_payments_table.html](templates/admin/pending_payments_table.html#L24-L45)
- [templates/admin/pending_payments_preview.html](templates/admin/pending_payments_preview.html#L64-L100)

**CSS Class:** `.section-header-with-border`

**HTML Structure:**
```html
<div class="section-header-with-border">
    <i class="fas fa-credit-card"></i>
    <h2>Pending Payments</h2>
</div>
```

**CSS Styling:**
```css
.section-header-with-border {
    padding: 1.5rem 2rem;
    background: #111827;
    border-left: 4px solid #f59e0b;      /* AMBER border */
    display: flex;
    align-items: center;
    gap: 0.75rem;
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
}

.section-header-with-border h2 {
    font-family: 'Playfair Display', serif;
    font-size: 1.5rem;
    color: #ffffff;
    margin: 0;
    font-weight: 700;
}

.section-header-with-border i {
    color: #c9a84c;          /* GOLD icon */
    font-size: 1.5rem;
}
```

**Visual Style:** Dark background with gold left border and gold icon

---

## 2. RECENT BOOKINGS - Blue Gradient Header
**Files:**
- [templates/admin/recent_bookings_table.html](templates/admin/recent_bookings_table.html#L25-L60)
- [templates/admin/recent_bookings_preview.html](templates/admin/recent_bookings_preview.html#L64-L100)

**CSS Class:** `.section-header-gradient`

**HTML Structure:**
```html
<div class="section-header-gradient">
    <div class="header-left">
        <i class="fas fa-bookmark"></i>
        <h2>Recent Bookings</h2>
    </div>
    <a href="#" class="view-all-btn">View All</a>
</div>
```

**CSS Styling:**
```css
.section-header-gradient {
    padding: 1.5rem 2rem;
    background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);  /* BLUE gradient */
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
}

.header-left {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.section-header-gradient h2 {
    font-family: 'Playfair Display', serif;
    font-size: 1.5rem;
    color: #ffffff;
    margin: 0;
    font-weight: 700;
}

.section-header-gradient i {
    color: #ffffff;              /* WHITE icon */
    font-size: 1.5rem;
}

.view-all-btn {
    color: #c9a84c;
    text-decoration: none;
    font-size: 0.9rem;
    font-weight: 600;
    transition: all 0.3s ease;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    position: relative;
}

.view-all-btn::after {
    content: '';
    position: absolute;
    bottom: -4px;
    left: 0;
    width: 0;
    height: 2px;
    background: #c9a84c;
    transition: width 0.3s ease;
}

.view-all-btn:hover::after {
    width: 100%;
}
```

**Visual Style:** Blue gradient background with white icons and gold "View All" link

---

## 3. FORM SECTION HEADERS - Solid Blue
**Files:**
- [templates/admin/room_form_admin.html](templates/admin/room_form_admin.html#L57-L73)

**CSS Class:** `.form-section-header`

**HTML Structure:**
```html
<div class="form-section-header">
    <i class="fas fa-door-open"></i>
    Basic Information
</div>
```

**CSS Styling:**
```css
.form-section-header {
    background: #2563eb;                /* SOLID BLUE */
    padding: 1rem 1.5rem;
    color: #ffffff;
    font-family: 'Playfair Display', serif;
    font-size: 1.25rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.form-section-header i {
    font-size: 1.5rem;
}
```

**Visual Style:** Solid blue background with white text

---

## 4. CARD HEADERS - Standalone Blue Headers
**Files:**
- [templates/admin/booking_management.html](templates/admin/booking_management.html#L14-L22)
- [templates/admin/payment_management.html](templates/admin/payment_management.html#L24-L32)
- [templates/admin/room_management.html](templates/admin/room_management.html#L14-L22)
- [templates/staff/staff_base.html](templates/staff/staff_base.html#L348-L365)
- [templates/guest/guest_base.html](templates/guest/guest_base.html#L338-L355)

**CSS Class:** `.luxury-card-header`

**HTML Structure:**
```html
<div class="luxury-card-header">
    <i class="fas fa-list"></i> Section Title
</div>
```

**CSS Styling:**
```css
.luxury-card-header {
    background: var(--blue-header);     /* #2563eb */
    padding: 1rem 1.5rem;
    color: #ffffff;
    font-family: 'Playfair Display', serif;
    font-size: 1.1rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    border-bottom: 2px solid rgba(37, 99, 235, 0.5);  /* Subtle border */
}
```

**Visual Style:** Blue background with subtle blue border at bottom, used on management pages and staff/guest dashboards

---

## 5. PAGE HEADER - Simple Title Section
**Files:**
- [templates/admin/admin_base.html](templates/admin/admin_base.html#L234-L246)
- [templates/staff/staff_base.html](templates/staff/staff_base.html#L563-L578)
- [templates/guest/guest_base.html](templates/guest/guest_base.html#L553-L568)

**CSS Class:** `.page-header`

**HTML Structure:**
```html
<div class="page-header">
    <h1>Dashboard Overview</h1>
    <p>Welcome back to your hotel management system</p>
</div>
```

**CSS Styling:**
```css
.page-header {
    margin-bottom: 2rem;
}

.page-header h1 {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
}

.page-header p {
    color: var(--text-muted);
    margin: 0;
}
```

**Visual Style:** Simple text-based page title with description, no background

---

## 6. SIMPLE SECTION TITLE - Bordered Underline
**Files:**
- [templates/staff/check_in_checkout.html](templates/staff/check_in_checkout.html#L8-L11)
- [templates/staff/dashboard.html](templates/staff/dashboard.html) - uses inline styling

**CSS Class:** `.section-title`

**HTML Structure:**
```html
<h3 class="section-title">
    <i class="fas fa-sign-in-alt"></i> Today's Check-Ins
</h3>
```

**CSS Styling:**
```css
.section-title {
    color: var(--text-light);
    font-weight: 700;
    margin-top: 2rem;
    margin-bottom: 1.5rem;
    border-bottom: 2px solid var(--gold);   /* GOLD underline */
    padding-bottom: 0.5rem;
}
```

**Visual Style:** Simple heading with gold underline

---

## Inconsistencies Found

| Issue | Current State | Locations |
|-------|---------------|-----------|
| **Different border colors** | Gold border vs. Blue gradient vs. Solid blue | Pending Payments (gold), Recent Bookings (blue gradient), Forms (solid blue) |
| **Different sizes** | Font sizes vary from 1rem to 1.5rem | Form headers (1.25rem) vs. Table headers (1.5rem) |
| **Icon colors inconsistent** | Gold icons vs. white icons vs. no icons | Pending Payments (gold), Recent Bookings (white) |
| **Padding variations** | Different padding schemes | 1rem vs. 1.5rem |
| **Border styles** | Left border vs. gradient vs. bottom border | Left border (Pending), Gradient (Bookings), Bottom border (Cards) |

---

## Recommendations for Standardization

### Option 1: Use `.section-header-gradient` for All Table Headers
- Apply to both Pending Payments and Recent Bookings tables
- Create variant colors for different sections (gold gradient, blue gradient)
- Keeps the professional appearance with gradient

### Option 2: Create a Unified `.section-header` Class
```css
.section-header {
    padding: 1.5rem 2rem;
    background: #111827;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
    font-family: 'Playfair Display', serif;
    font-size: 1.5rem;
    color: #ffffff;
    font-weight: 700;
}

/* Variants */
.section-header.gold {
    border-left: 4px solid #f59e0b;
}

.section-header.gold i {
    color: #c9a84c;
}

.section-header.blue {
    background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);
}

.section-header.blue i {
    color: #ffffff;
}
```

### Option 3: Keep Section-Specific but Document Clearly
- Document when to use each style (table vs. form vs. card)
- Create a component library reference
- Ensure all new pages follow the established pattern

---

## Files Needing Updates
1. [templates/admin/pending_payments_table.html](templates/admin/pending_payments_table.html) - Standardize header
2. [templates/admin/recent_bookings_table.html](templates/admin/recent_bookings_table.html) - Standardize header
3. [templates/admin/room_form_admin.html](templates/admin/room_form_admin.html) - Consider unifying with table headers
4. All management pages using `.luxury-card-header` - Ensure consistency
5. Documentation - Create a component style guide

---

## Color Reference
- **Gold**: `#c9a84c`
- **Gold Amber**: `#f59e0b`
- **Blue Primary**: `#2563eb`
- **Blue Dark**: `#1d4ed8`, `#1e40af`
- **Background Dark**: `#111827`, `#0a0f1e`
- **Text Light**: `#ffffff`, `#e5e7eb`
- **Text Muted**: `#9ca3af`, `#6b7280`
