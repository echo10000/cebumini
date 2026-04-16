# Cebu Luxury Hotel - Admin Dashboard Design Documentation

## Overview
The Cebu Luxury Hotel admin dashboard has been completely redesigned with a sophisticated dark theme featuring navy, gold, and elegant typography to match the luxury hospitality brand.

## Color Palette

### Primary Colors
- **Dark Navy**: `#0a0f1e` - Main sidebar and navbar background
- **Light Dark**: `#111827` - Main content area background
- **Gold**: `#c9a84c` - Primary accent color for highlights and interactive elements
- **Gold Dark**: `#a68a3a` - Darker shade for hover states

### Text Colors
- **Light Text**: `#e5e7eb` - Primary text color on dark backgrounds
- **Muted Text**: `#9ca3af` - Secondary text and descriptions

### Status Colors
- **Success**: `#10b981` - Confirmed/completed status
- **Warning**: `#f59e0b` - Pending/warning status
- **Danger**: `#dc2626` - Failed/cancelled status
- **Info**: `#3b82f6` - Information/additional status

## Typography

### Font Families
- **Headings**: "Playfair Display" (serif) - 700, 800, 900 weights
  - Elegant, luxury aesthetic
  - Used for all H1-H6 elements and page titles
  
- **Body Text**: "DM Sans" (sans-serif) - 400, 500, 700 weights
  - Clean, modern readability
  - Used for all body content and labels

### Font Sizes & Hierarchy
- Page Title (H1): 2.5rem
- Section Title (H5): 1.25rem
- Body Text: 1rem (16px default)
- Small Text: 0.85-0.9rem
- Labels: 0.9rem

## Layout Architecture

### Navigation Structure

#### Top Navbar
- **Position**: Fixed at top (z-index: 1030)
- **Height**: 70px
- **Background**: Dark navy (#0a0f1e)
- **Border**: 3px solid gold bottom border
- **Content**:
  - Left: Hotel logo + "CEBU LUXURY" text
  - Right: User profile + Logout button
  - Shadow: 0 4px 12px rgba(0, 0, 0, 0.3)

#### Sidebar
- **Position**: Fixed left side, below navbar
- **Width**: 260px
- **Height**: calc(100vh - 70px)
- **Background**: Dark navy (#0a0f1e)
- **Sections**:
  - Dashboard
  - Management (Payments, Bookings, Rooms, Users)
  - Reports
  - Other (Back to Hotel)
- **Active State**: Gold text with gold right border
- **Hover State**: Gold text with gold background tint
- **Shadow**: 2px 0 8px rgba(0, 0, 0, 0.3)

#### Main Content Area
- **Margin-left**: 260px (accounts for sidebar)
- **Margin-top**: 70px (accounts for navbar)
- **Background**: Light dark (#111827)
- **Padding**: 2rem
- **Min-height**: calc(100vh - 70px)

### Components

#### Stat Cards (dashboard.html)
- **Class**: `.stat-card`
- **Background**: Card background (#1a202c)
- **Border**: 1px solid rgba(201, 168, 76, 0.2)
- **Border Radius**: 12px
- **Padding**: 1.5rem
- **Top Border Animation**: 4px gold bar appears on hover
- **Features**:
  - Icon area with gold color
  - Label text in muted color
  - Large value in gold
  - Subtext in muted color
  - Smooth hover effect with lift (translateY -4px)

#### Admin Cards (generic container)
- **Class**: `.admin-card`
- **Background**: Card background (#1a202c)
- **Border**: 1px solid rgba(gold, 0.2)
- **Border Radius**: 12px
- **Header**: Gradient background with gold bottom border
- **Body**: 1.5rem padding

#### Tables (admin-table)
- **Class**: `.admin-table`
- **Background**: Card background
- **Header**: Gold text on gradient background
- **Rows**: Hover effect with light gold tint
- **Borders**: Gold accent on hover

#### Buttons

**Primary Button (.btn-luxury)**
- **Background**: Gold (#c9a84c)
- **Color**: Dark navy text
- **Padding**: 0.625rem 1.25rem
- **Border Radius**: 6px
- **Font Weight**: 600
- **Hover**: Darker gold with lift and shadow

**Outline Button (.btn-luxury-outline)**
- **Background**: Transparent
- **Color**: Gold
- **Border**: 2px solid gold
- **Hover**: Gold background with dark navy text

## Responsive Design

### Tablet & Mobile (max-width: 768px)
- Sidebar transforms into overlay menu
- Transform translateX(-100%) by default, shown on toggle
- Main container removes left margin
- Reduced padding
- User profile hidden on mobile
- Font sizes adjusted for smaller screens

### Responsive Classes
- **Grid**: Bootstrap 5 grid system (col-md-6, col-lg-3, etc.)
- **Gap utilities**: g-4 for grid spacing
- **Flexbox**: d-flex with gap classes

## Key Features

### Navigation
1. **Active State Indicator**: Gold color + gold right border
2. **Badge Notifications**: Red badges for pending notifications
3. **Icon Support**: Font Awesome icons throughout
4. **Smooth Transitions**: 0.3s ease transitions on all interactive elements

### Data Display
1. **Stat Cards**: Display key metrics with icons
2. **Tables**: Responsive tables with proper theming
3. **Status Badges**: Color-coded status indicators
4. **Dividers**: Subtle gold gradient dividers between sections

### Interactive Elements
1. **Buttons**: Multiple button styles and states
2. **Forms**: Styled inputs, selects, and labels with gold accents
3. **Dropdowns**: Custom styled dropdowns with gold accents
4. **Modals**: Themed modal dialogs

### Visual Hierarchy
1. **Headers**: Large Playfair Display font
2. **Accent Color**: Gold used to highlight important elements
3. **Negative Space**: Proper padding and margins
4. **Visual Feedback**: Hover states on all interactive elements

## Implementation Files

### Templates
- **admin_base.html**: Base template with navbar, sidebar, and main layout
- **dashboard.html**: Main dashboard overview
- **booking_management.html**: Booking management table
- **payment_management.html**: Payment management table

### Styling
- **admin_base.html**: Contains all CSS in `<style>` block (~800+ lines)
- **admin_luxury.css**: Additional form and component styling

### Fonts
- Google Fonts API included in admin_base.html:
  - Playfair Display (700, 800, 900)
  - DM Sans (400, 500, 700)

## CSS Variables (Custom Properties)

```css
:root {
    --dark-navy: #0a0f1e;
    --light-dark: #111827;
    --gold: #c9a84c;
    --gold-dark: #a68a3a;
    --text-light: #e5e7eb;
    --text-muted: #9ca3af;
    --card-bg: #1a202c;
}
```

## Accessibility Considerations

1. **Color Contrast**: Light text on dark background meets WCAG AA standards
2. **Focus States**: Clear focus indicators on form elements
3. **Semantic HTML**: Proper heading hierarchy and landmark regions
4. **Screen Reader**: Appropriate alt text and ARIA labels (where needed)
5. **Keyboard Navigation**: All interactive elements are keyboard accessible

## Performance Optimizations

1. **CSS-in-JS**: Minimal HTTP requests (no external CSS file)
2. **Google Fonts**: Limited to 2 fonts with 6 weights total
3. **Animations**: GPU-accelerated transitions using transform/opacity
4. **Flexbox/Grid**: Modern layout without unnecessary DOM elements

## Browser Compatibility

- Modern browsers (Chrome, Firefox, Safari, Edge)
- CSS Grid and Flexbox support required
- CSS Variables support required
- Fallbacks available where needed

## Future Enhancements

1. **Dark Mode Toggle**: Already using dark theme; can add light mode option
2. **Sidebar Collapse**: Animation to collapse sidebar for more content space
3. **Advanced Charts**: Integration with charting libraries
4. **Data Export**: Excel/PDF export functionality
5. **Real-time Notifications**: WebSocket integration for live updates
6. **Mobile App**: Native mobile application using same design system

## Usage Instructions

### For Developers

1. **Extending the Base Template**:
   ```html
   {% extends 'admin/admin_base.html' %}
   {% block content %}
   <!-- Your content here -->
   {% endblock %}
   ```

2. **Using Utility Classes**:
   - `.text-gold`: Gold text color
   - `.border-gold`: Gold border
   - `.stat-card`: Statistics display card
   - `.admin-card`: Content card with header
   - `.btn-luxury`: Primary button
   - `.btn-luxury-outline`: Outline button
   - `.badge-notification`: Status badge

3. **Responsive Spacing**:
   - Use Bootstrap grid: `col-md-6 col-lg-3`
   - Use gap classes: `g-4` for grid spacing

### For Designers

1. **Color Selections**: Refer to color palette for consistency
2. **Typography**: Use Playfair Display for headings, DM Sans for body
3. **Components**: Reference existing component examples
4. **Icons**: Use Font Awesome 6.4.0
5. **Spacing**: Follow 8px spacing system (multiples of 8)

## Maintenance Notes

1. **Google Fonts API**: Ensure CDN link is active
2. **Font Awesome CDN**: Keep version 6.4.0 updated
3. **Bootstrap CSS**: Included for form reset and utilities
4. **Browser Testing**: Test on Chrome, Firefox, Safari, Edge
5. **Mobile Testing**: Test on iOS Safari and Chrome Mobile

---

Last Updated: April 15, 2026
Design System Version: 1.0
Cebu Luxury Hotel Management System
