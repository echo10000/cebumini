# Luxury Hotel Stat Cards - Implementation Guide

## Overview
Four elegant, responsive stat cards designed specifically for the Cebu Luxury Hotel admin dashboard. Each card features an icon, label, large value, and description with smooth hover effects.

## Card Specifications

### Visual Design
| Property | Value |
|----------|-------|
| **Background Color** | #1a2235 (Dark Blue-Gray) |
| **Left Border** | 4px solid #c9a84c (Gold) |
| **Border Radius** | 12px |
| **Padding** | 1.75rem |
| **Icon Color** | #c9a84c (Gold) |
| **Label Color** | #ffffff (White) |
| **Value Color** | #c9a84c (Gold) |
| **Description Color** | #9ca3af (Muted Gray) |

### The 4 Cards

#### 1. Total Revenue
- **Icon**: Peso Sign (`fas fa-peso-sign`)
- **Label**: "Total Revenue"
- **Value Example**: ₱2.4M
- **Description**: "All-time earnings from bookings"
- **Data Source**: `{{ total_revenue|floatformat:2 }}`

#### 2. Confirmed Bookings
- **Icon**: Calendar Check (`fas fa-calendar-check`)
- **Label**: "Confirmed Bookings"
- **Value Example**: 1,284
- **Description**: "Total confirmed reservations"
- **Data Source**: `{{ confirmed_bookings }}`

#### 3. Pending Payments
- **Icon**: Hourglass Half (`fas fa-hourglass-half`)
- **Label**: "Pending Payments"
- **Value Example**: 47
- **Description**: "Awaiting customer verification"
- **Data Source**: `{{ pending_payments }}`

#### 4. Occupancy Rate
- **Icon**: Door Open (`fas fa-door-open`)
- **Label**: "Occupancy Rate"
- **Value Example**: 87.5%
- **Description**: "Current room occupancy percentage"
- **Data Source**: `{{ occupancy_rate|floatformat:1 }}%`

## Styling Features

### 1. Layout
- **Grid System**: CSS Grid with `repeat(auto-fit, minmax(280px, 1fr))`
- **Gap**: 1.5rem between cards
- **Responsive**: 4 columns on desktop, 2 columns on tablet, 1 column on mobile

### 2. Icon Positioning
- **Location**: Top-left of card
- **Size**: 2.5rem (desktop), scales down on smaller screens
- **Color**: Gold (#c9a84c)
- **Spacing Below**: 1rem margin

### 3. Typography
- **Label**: 0.9rem, uppercase, 0.5px letter-spacing
- **Value**: 2.25rem, Playfair Display font (serif), gold color
- **Description**: 0.85rem, muted gray color

### 4. Hover Effects
**On Hover:**
- Left border color brightens to #e6c76e
- Card lifts up with `transform: translateY(-8px)`
- **Gold Glow Box Shadow:**
  ```css
  box-shadow: 0 20px 40px rgba(201, 168, 76, 0.25),
              0 0 30px rgba(201, 168, 76, 0.15);
  ```
- Smooth transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1)

### 5. Subtle Background Effect
- Radial gradient in top-right corner
- Light gold glow: `rgba(201, 168, 76, 0.05)`
- Radius: 150px
- Non-interactive (pointer-events: none)

## Responsive Breakpoints

### Desktop (1200px+)
- Grid: 4 columns
- Gap: 1.5rem
- Padding: 1.75rem
- Icon: 2.5rem
- Value: 2.25rem

### Tablet (768px - 1024px)
- Grid: 2-3 columns
- Gap: 1.25rem
- Padding: 1.5rem
- Icon: 2rem
- Value: 1.875rem

### Mobile (< 768px)
- Grid: 1 column
- Gap: 1rem
- Padding: 1.25rem
- Icon: 1.75rem
- Value: 1.625rem
- Label: 0.8rem
- Description: 0.75rem

## Implementation Methods

### Method 1: Include in HTML/Template
Simply copy the stat cards HTML and CSS into your template. Example:

```html
<div class="luxury-stat-cards">
    <div class="stat-card-luxury">
        <div class="stat-icon">
            <i class="fas fa-peso-sign"></i>
        </div>
        <div class="stat-label">Total Revenue</div>
        <div class="stat-value">₱{{ total_revenue|floatformat:2 }}</div>
        <div class="stat-description">All-time earnings from bookings</div>
    </div>
    <!-- Other cards... -->
</div>
```

### Method 2: Django Template Loop (Dynamic)
Pass data from your view and use a template loop:

```python
# In your view
context = {
    'stats': [
        {
            'icon': 'peso-sign',
            'label': 'Total Revenue',
            'value': f'₱{total_revenue:,.2f}',
            'description': 'All-time earnings from bookings'
        },
        # ... more stats
    ]
}
```

```html
<!-- In template -->
<div class="luxury-stat-cards">
    {% for stat in stats %}
    <div class="stat-card-luxury">
        <div class="stat-icon">
            <i class="fas fa-{{ stat.icon }}"></i>
        </div>
        <div class="stat-label">{{ stat.label }}</div>
        <div class="stat-value">{{ stat.value }}</div>
        <div class="stat-description">{{ stat.description }}</div>
    </div>
    {% endfor %}
</div>
```

## Browser Compatibility
- ✅ Chrome/Chromium (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Edge (latest)
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

## Performance Considerations
1. **GPU Acceleration**: Uses `transform` for animations (not `left`/`top`)
2. **Smooth Transitions**: Hardware-accelerated with `cubic-bezier` timing function
3. **No Layout Thrashing**: CSS Grid handles layout efficiently
4. **Font Loading**: Google Fonts loaded with `display=swap` for fast rendering

## Font Awesome Icon Suggestions

| Metric | Icon | Class |
|--------|------|-------|
| Revenue | Peso Sign | `fas fa-peso-sign` |
| Bookings | Calendar Check | `fas fa-calendar-check` |
| Bookings Alt | Bookmark | `fas fa-bookmark` |
| Payments | Credit Card | `fas fa-credit-card` |
| Pending | Hourglass | `fas fa-hourglass-half` |
| Occupancy | Door Open | `fas fa-door-open` |
| Rooms | Bed | `fas fa-bed` |
| Guests | Users | `fas fa-users` |
| Revenue Alt | Chart Bar | `fas fa-chart-bar` |
| Rating | Star | `fas fa-star` |

## Color Psychology in Luxury Context

| Color | Psychology | Usage |
|-------|-----------|-------|
| Dark Blue-Gray (#1a2235) | Trustworthy, Professional | Card background |
| Gold (#c9a84c) | Luxury, Premium, Wealth | Accents, values, highlights |
| White (#ffffff) | Clean, Clarity | Labels, text |
| Muted Gray (#9ca3af) | Secondary info, Balance | Descriptions |

## Customization Examples

### Change All Gold Accents to Silver
Replace `#c9a84c` with `#a3a3a3` in the CSS

### Add More Cards
Duplicate the card div and update content:
```html
<div class="stat-card-luxury">
    <div class="stat-icon">
        <i class="fas fa-star"></i>
    </div>
    <div class="stat-label">Guest Ratings</div>
    <div class="stat-value">4.8★</div>
    <div class="stat-description">Average satisfaction score</div>
</div>
```

### Make Cards Clickable
Wrap entire card in a link:
```html
<a href="/admin/revenue/" style="text-decoration: none; color: inherit;">
    <div class="stat-card-luxury">
        <!-- Card content -->
    </div>
</a>
```

### Add Trend Indicators
Add a small sparkline or trending badge:
```html
<div class="stat-card-luxury">
    <!-- ... existing content ... -->
    <div style="margin-top: 1rem; font-size: 0.8rem; color: #10b981;">
        <i class="fas fa-arrow-up"></i> 12% vs last month
    </div>
</div>
```

## Files Provided

1. **stat_cards_component.html**
   - Reusable component with inline CSS and comments
   - Includes usage instructions and Django template example
   - Ready to copy into your project

2. **stat_cards_preview.html**
   - Standalone HTML file for previewing cards
   - Open in browser to see live demo with hover effects
   - Full featured with features section and documentation

3. **dashboard.html** (Updated)
   - Integrated luxury stat cards into admin dashboard
   - Uses dynamic Django template variables
   - Part of the complete admin dashboard design

## Testing Checklist

- [ ] Cards display correctly on desktop (1200px+)
- [ ] Cards display correctly on tablet (768px - 1024px)
- [ ] Cards display correctly on mobile (< 768px)
- [ ] Hover effect triggers smoothly
- [ ] Gold glow shadow appears on hover
- [ ] Card lifts up animation works
- [ ] Icons render correctly
- [ ] All text is readable
- [ ] Responsive behavior works as expected
- [ ] Works on different browsers

## Accessibility Notes

1. **Color Contrast**: Gold text on dark background meets WCAG AA standards
2. **Font Size**: Base 16px ensures readability
3. **Icon Semantics**: Icons are decorative, text is always present
4. **Keyboard Navigation**: No interactive elements (can be added if needed)
5. **Screen Readers**: Text labels are clear and descriptive

## Future Enhancements

1. **Click to Expand**: Make cards clickable to show detailed view
2. **Chart Mini**: Add tiny sparkline chart to each card
3. **Trending**: Add "↑ 12%" badge showing change from previous period
4. **Animations**: Stagger animation when page loads
5. **Dark/Light Mode**: Easy toggle for light theme variant
6. **Real-time Updates**: WebSocket integration for live data

## Support & Variations

### Mini Card Version (Sidebar)
```html
<div class="stat-card-luxury" style="padding: 1rem;">
    <div class="stat-icon" style="font-size: 1.5rem;"></div>
    <div class="stat-value" style="font-size: 1.5rem;"></div>
</div>
```

### Wide Card Version (Full Width)
```html
<div class="luxury-stat-cards" style="grid-template-columns: 1fr;">
    <!-- Cards will be full width -->
</div>
```

## Questions & Support
For implementation questions, refer to:
- stat_cards_component.html - Component documentation
- stat_cards_preview.html - Visual reference
- ADMIN_DASHBOARD_DESIGN.md - Overall dashboard design

---

**Design System Version**: 1.0  
**Last Updated**: April 15, 2026  
**Created For**: Cebu Luxury Hotel Admin Dashboard
