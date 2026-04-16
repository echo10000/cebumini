# Cebu Luxury Hotel - Admin Dashboard Quick Reference Guide

## Color Scheme
| Purpose | Color | Hex Code |
|---------|-------|----------|
| Sidebar & Navbar | Dark Navy | `#0a0f1e` |
| Main Content Background | Light Dark | `#111827` |
| Primary Accent (Buttons, Highlights) | Gold | `#c9a84c` |
| Hover Accent | Dark Gold | `#a68a3a` |
| Primary Text | Light | `#e5e7eb` |
| Secondary Text | Muted | `#9ca3af` |
| Card Background | Dark Blue-Gray | `#1a202c` |

## Typography
- **Headings**: Playfair Display (serif) - 700/800/900
- **Body Text**: DM Sans (sans-serif) - 400/500/700

## Key Elements

### Fixed Top Navigation Bar (70px height)
- Dark navy background with gold 3px bottom border
- Logo + "CEBU LUXURY" text on left
- User profile + logout button on right
- Position: fixed, z-index: 1030

### Fixed Left Sidebar (260px width)
- Dark navy background
- Navigation sections with gold text for active items
- Position: fixed, starts at 70px from top
- Responsive: transforms to overlay on mobile

### Main Content Area
- Background: Light dark (#111827)
- Margin-left: 260px (for sidebar)
- Margin-top: 70px (for navbar)
- Padding: 2rem

### Stat Cards
- Background: Dark card background
- Border: 1px solid gold accent
- Icon: Gold color (2.5rem size)
- Value: Gold color (2rem font size)
- Hover: Slight lift animation + gold top bar appears

### Tables
- Header: Gold text on light background
- Rows: Hover with light gold tint
- Borders: Subtle gold accents

### Buttons
- **Primary (.btn-luxury)**: Gold background, dark text, shadow on hover
- **Outline (.btn-luxury-outline)**: Transparent with gold border, fills on hover

## CSS Variables Available
```css
--dark-navy: #0a0f1e
--light-dark: #111827
--gold: #c9a84c
--gold-dark: #a68a3a
--text-light: #e5e7eb
--text-muted: #9ca3af
--card-bg: #1a202c
```

## Using the Template

### Extend from admin base in any admin page:
```html
{% extends 'admin/admin_base.html' %}

{% block title %}Page Title - Cebu Luxury{% endblock %}

{% block content %}
  <!-- Your content here -->
  <div class="page-header">
    <h1>Page Title</h1>
    <p>Optional subtitle</p>
  </div>
  
  <!-- Stat cards -->
  <div class="row mb-4 g-4">
    <div class="col-md-6 col-lg-3">
      <div class="stat-card">
        <div class="stat-icon"><i class="fas fa-icon"></i></div>
        <div class="stat-label">Label</div>
        <div class="stat-value">123</div>
        <div class="stat-subtext">Subtext</div>
      </div>
    </div>
  </div>
  
  <!-- Content card -->
  <div class="admin-card">
    <div class="admin-card-header">
      <h5><i class="fas fa-icon"></i> Section Title</h5>
    </div>
    <div class="admin-card-body">
      <!-- Card content -->
    </div>
  </div>
{% endblock %}
```

## Utility Classes

| Class | Purpose |
|-------|---------|
| `.page-header` | Page title section |
| `.stat-card` | Statistics display card |
| `.admin-card` | Content container |
| `.admin-card-header` | Card header with gold accent |
| `.admin-card-body` | Card body content |
| `.admin-table` | Table container |
| `.btn-luxury` | Primary gold button |
| `.btn-luxury-outline` | Outlined button |
| `.badge-notification` | Status badge |
| `.text-gold` | Gold text |
| `.border-gold` | Gold border |
| `.gold-divider` | Decorative divider |

## Layout Grid

### Responsive Breakpoints
- **lg**: 4 columns per row (col-lg-3)
- **md**: 2 columns per row (col-md-6)
- **sm**: 1 column per row (stacks)

### Spacing
- Use Bootstrap gap classes: `g-4` for grid gaps
- Padding: 1.5rem standard for card bodies
- Margins: 2rem for section spacing

## Files Modified

1. **admin_base.html** (NEW)
   - Base template with navbar, sidebar, and styling
   - All CSS included inline
   - Responsive design

2. **admin/dashboard.html** (UPDATED)
   - Now extends admin_base.html
   - Updated to use new luxury components
   - Redesigned stat cards and layout

3. **admin/booking_management.html** (UPDATED)
   - Now extends admin_base.html
   - Updated table styling
   - New filter section design

4. **admin/payment_management.html** (UPDATED)
   - Now extends admin_base.html
   - Updated table styling
   - New filter section design

5. **admin_luxury.css** (NEW)
   - Additional form and component styling
   - Can be used for static file setup later

## Important Notes

### Responsive Behavior
- On tablets/mobile, sidebar converts to an overlay
- Main content takes full width when sidebar is hidden
- All text sizes adjust for smaller screens
- Forms display at 16px minimum on mobile (for zoom issues)

### Customization Tips

1. **Change Colors**: Modify CSS variables in admin_base.html `<style>` block
2. **Adjust Spacing**: Change padding/margin values in card/button styles
3. **Font Changes**: Update Google Fonts link and font-family values
4. **Add Icons**: Use Font Awesome 6.4.0 icons with `<i class="fas fa-..."></i>`
5. **New Pages**: Create template that extends admin_base.html

### Browser Performance
- CSS variables for easy theming
- Hardware-accelerated animations (transform/opacity)
- Minimal repaints with efficient selectors
- Google Fonts optimized with display=swap

## Status Colors
- Success: `#10b981` - Confirmed/completed
- Warning: `#f59e0b` - Pending
- Danger: `#dc2626` - Failed/cancelled
- Info: `#3b82f6` - Informational

## Future Enhancements
- Implement static CSS file setup
- Add sidebar collapse animation
- Create light mode variant
- Add advanced data visualization
- Implement real-time notifications

---
For detailed information, see: ADMIN_DASHBOARD_DESIGN.md
Last Updated: April 15, 2026
