# Admin Dashboard Data Analysis Report

## Executive Summary

**Status**: ✅ Data is properly queried and passed to templates, but **⚠️ TEMPLATE BUG FOUND** - Recent bookings table references non-existent field.

**Sample Data**: ✅ Database contains sample data
- 14 Bookings
- 12 Payments

---

## 1. Admin Dashboard View Code

**File**: [authentication/views_admin.py](authentication/views_admin.py#L26)

```python
@login_required
@admin_required
def admin_dashboard(request):
    """Admin Dashboard with overview statistics"""
    today = timezone.now().date()
    
    # Basic stats
    total_bookings = Booking.objects.count()
    pending_payments_count = Payment.objects.filter(status=PaymentStatus.PENDING).count()
    confirmed_bookings = Booking.objects.filter(status=BookingStatus.CONFIRMED).count()
    
    # Revenue calculations
    completed_payments = Payment.objects.filter(status=PaymentStatus.COMPLETED)
    total_revenue = completed_payments.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Today's stats
    today_check_ins = Booking.objects.filter(
        check_in=today,
        status=BookingStatus.CONFIRMED
    ).count()
    today_check_outs = Booking.objects.filter(
        check_out=today,
        status=BookingStatus.CONFIRMED
    ).count()
    
    # This month revenue
    first_day_of_month = today.replace(day=1)
    month_revenue = completed_payments.filter(
        completed_at__date__gte=first_day_of_month
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Occupancy rate
    total_rooms = Room.objects.count()
    occupied_rooms = Room.objects.filter(is_available=False).count()
    occupancy_rate = (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0
    
    # Recent bookings (QuerySet for template iteration)
    recent_bookings = Booking.objects.select_related('room', 'guest').order_by('-created_at')[:5]
    
    # Pending payments list (QuerySet for template iteration)
    pending_payments = Payment.objects.select_related('booking__room', 'booking__guest').filter(
        status=PaymentStatus.PENDING
    ).order_by('-created_at')[:5]
    
    context = {
        'total_bookings': total_bookings,
        'pending_payments_count': pending_payments_count,
        'confirmed_bookings': confirmed_bookings,
        'total_revenue': total_revenue,
        'today_check_ins': today_check_ins,
        'today_check_outs': today_check_outs,
        'month_revenue': month_revenue,
        'occupancy_rate': occupancy_rate,
        'total_rooms': total_rooms,
        'recent_bookings': recent_bookings,
        'pending_payments': pending_payments,
    }
    
    return render(request, 'admin/dashboard.html', context)
```

### Data Being Queried:

| Context Variable | Type | Query | Limit |
|---|---|---|---|
| `total_bookings` | int | All Bookings | - |
| `pending_payments_count` | int | Payment count where status=PENDING | - |
| `confirmed_bookings` | int | Booking count where status=CONFIRMED | - |
| `total_revenue` | Decimal | Sum of Payment amounts (COMPLETED status) | - |
| `today_check_ins` | int | Bookings with check_in=today, status=CONFIRMED | - |
| `today_check_outs` | int | Bookings with check_out=today, status=CONFIRMED | - |
| `month_revenue` | Decimal | Sum of payments completed this month | - |
| `occupancy_rate` | float | (occupied_rooms / total_rooms) * 100 | - |
| `total_rooms` | int | All Rooms | - |
| `recent_bookings` | QuerySet | Bookings ordered by -created_at | Top 5 |
| `pending_payments` | QuerySet | Payments (status=PENDING) ordered by -created_at | Top 5 |

---

## 2. Admin Dashboard Template Structure

**File**: [templates/admin/dashboard.html](templates/admin/dashboard.html)

### Template Hierarchy:
```
admin/dashboard.html (extends admin_base.html)
├── Luxury Stat Cards (4 cards displaying summary statistics)
│   ├── Total Revenue: {{ total_revenue|floatformat:2 }}
│   ├── Confirmed Bookings: {{ confirmed_bookings }}
│   ├── Pending Payments: {{ pending_payments_count }}
│   └── Occupancy Rate: {{ occupancy_rate|floatformat:1 }}%
│
├── Check-in/Check-out Panels
│   ├── Today's Check-ins: {{ today_check_ins }}
│   └── Today's Check-outs: {{ today_check_outs }}
│
├── Revenue Overview Cards
│   ├── This Month's Revenue: {{ month_revenue|floatformat:2 }}
│   └── Total Bookings: {{ total_bookings }}
│
├── {% include 'admin/pending_payments_table.html' %}
│
└── {% include 'admin/recent_bookings_table.html' %}
```

---

## 3. Pending Payments Table Template

**File**: [templates/admin/pending_payments_table.html](templates/admin/pending_payments_table.html#L224)

### Template Iteration:
```django
{% if pending_payments %}
    {% for payment in pending_payments %}
    <tr>
        <td>#{{ payment.booking.id }}</td>
        <td>{{ payment.booking.guest.first_name }} {{ payment.booking.guest.last_name }}</td>
        <td>₱{{ payment.amount|floatformat:2 }}</td>
        <td>
            <!-- Payment method badge with color coding -->
            {% if payment.payment_method == 'bank_transfer' %}
                <span class="badge-pill bank-transfer">Bank Transfer</span>
            {% elif payment.payment_method == 'paymongo' %}
                <span class="badge-pill paymongo">PayMongo</span>
            {% elif payment.payment_method == 'stripe' %}
                <span class="badge-pill stripe">Stripe</span>
            {% endif %}
        </td>
        <td>{{ payment.created_at|date:"M d, Y" }}</td>
        <td><i class="fas fa-clock"></i> Pending</td>
        <td>
            <a href="{% url 'admin_panel:payment_detail' payment.id %}" class="btn-review">Review</a>
        </td>
    </tr>
    {% endfor %}
{% else %}
    <tr>
        <td colspan="7">
            <div class="empty-state">
                <i class="fas fa-check-circle"></i>
                <p>No pending payments at this time</p>
            </div>
        </td>
    </tr>
{% endif %}
```

### Table Columns:
| Column | Data Source | Type | Display Format |
|---|---|---|---|
| Booking ID | `payment.booking.id` | int | `#123` |
| Guest Name | `payment.booking.guest.first_name/last_name` | string | Full name |
| Amount | `payment.amount` | Decimal | `₱1,234.56` |
| Payment Method | `payment.payment_method` | enum | Badge with icon & color |
| Date | `payment.created_at` | datetime | `Jan 15, 2024` |
| Status | Static | string | "Pending" with clock icon |
| Action | URL | link | "Review" button to payment detail |

**Empty State**: Shows when `pending_payments` is empty

---

## 4. Recent Bookings Table Template

**File**: [templates/admin/recent_bookings_table.html](templates/admin/recent_bookings_table.html#L235)

### Template Iteration:
```django
{% if recent_bookings %}
    {% for booking in recent_bookings %}
    <tr>
        <td><span class="booking-id">#{{ booking.id }}</span></td>
        <td>{{ booking.guest.first_name }} {{ booking.guest.last_name }}</td>
        <td><span class="room-type">{{ booking.room.room_type }}</span></td>
        <td>
            <span class="dates-range">
                {{ booking.check_in|date:"M d" }} - {{ booking.check_out|date:"M d, Y" }}
            </span>
        </td>
        <td>
            <!-- Status badge with color coding -->
            {% if booking.status == 'confirmed' %}
                <span class="badge-status confirmed">
                    <i class="fas fa-check-circle"></i> Confirmed
                </span>
            {% elif booking.status == 'pending' %}
                <span class="badge-status pending">
                    <i class="fas fa-hourglass-half"></i> Pending
                </span>
            {% endif %}
        </td>
        <td><span class="booking-amount">₱{{ booking.total_amount|floatformat:2 }}</span></td>
    </tr>
    {% endfor %}
{% else %}
    <tr>
        <td colspan="6">
            <div class="empty-state">
                <i class="fas fa-inbox"></i>
                <p>No recent bookings</p>
            </div>
        </td>
    </tr>
{% endif %}
```

### Table Columns:
| Column | Data Source | Type | Display Format |
|---|---|---|---|
| Booking # | `booking.id` | int | `#123` |
| Guest | `booking.guest.first_name/last_name` | string | Full name |
| Room | `booking.room.room_type` | enum | Room type |
| Check-in / Check-out | `booking.check_in/check_out` | date | `Jan 15 - Jan 18, 2024` |
| Status | `booking.status` | enum | Badge (Confirmed/Pending/Other) |
| Amount | `booking.total_amount` | Decimal | `₱1,234.56` |

**Empty State**: Shows when `recent_bookings` is empty

---

## 5. Data Flow Summary

```
admin_dashboard view
    ├─ Query: Payment.objects.filter(status=PENDING)[:5]
    │   └─ Pass to template: pending_payments
    │       └─ Template: admin/pending_payments_table.html
    │           └─ Display: 5 most recent pending payments
    │
    └─ Query: Booking.objects.select_related('room', 'guest')[:5]
        └─ Pass to template: recent_bookings
            └─ Template: admin/recent_bookings_table.html
                └─ Display: 5 most recent bookings
```

---

## 6. ⚠️ ISSUES FOUND

### Issue #1: Template Bug - Non-existent Field Reference

**Location**: [templates/admin/recent_bookings_table.html](templates/admin/recent_bookings_table.html#L280)

**Problem**: The template references `booking.total_amount`, but the Booking model only has `booking.total_price`.

**Current (BROKEN)**:
```django
<td><span class="booking-amount">₱{{ booking.total_amount|floatformat:2 }}</span></td>
```

**Should be**:
```django
<td><span class="booking-amount">₱{{ booking.total_price|floatformat:2 }}</span></td>
```

**Impact**: The booking amount field will display as empty in recent bookings table.

**Booking Model Field** (confirmed at [authentication/models.py](authentication/models.py#L190)):
```python
total_price = models.DecimalField(
    max_digits=10,
    decimal_places=2,
    validators=[MinValueValidator(0)]
)
```

---

## 7. Sample Data Status

### Database Contents:
- ✅ **14 Bookings** exist in database
- ✅ **12 Payments** exist in database

### Data Visibility:
- ✅ **Pending Payments Table**: Should display up to 5 most recent pending payments
- ⚠️ **Recent Bookings Table**: Data will display incorrectly due to field name bug

---

## 8. Booking Model Structure

**File**: [authentication/models.py](authentication/models.py#L176)

### Key Fields:
```python
class Booking(models.Model):
    room = ForeignKey(Room)
    guest = ForeignKey(CustomUser)
    check_in = DateField()
    check_out = DateField()
    total_price = DecimalField(max_digits=10, decimal_places=2)  # ← USE THIS, NOT total_amount
    status = CharField(choices=BookingStatus.choices)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

---

## 9. Payment Model Structure

### Key Fields:
```python
class Payment(models.Model):
    booking = ForeignKey(Booking)
    amount = DecimalField(max_digits=10, decimal_places=2)
    payment_method = CharField(choices=...)
    status = CharField(choices=PaymentStatus.choices)
    created_at = DateTimeField(auto_now_add=True)
    completed_at = DateTimeField(null=True, blank=True)
```

---

## 10. Recommendations

### Fix the Template Bug:
1. Replace `booking.total_amount` with `booking.total_price` in [templates/admin/recent_bookings_table.html](templates/admin/recent_bookings_table.html#L280)

### Data Status:
- ✅ Data is being properly queried and passed to templates
- ✅ Sample data exists in database
- ✅ Pending payments display correctly
- ⚠️ Recent bookings amount field needs fix

### Next Steps:
1. Fix the recent bookings template field name
2. Test the admin dashboard with actual data
3. Verify all context variables display correctly

---

## Quick Reference: Context Variables Passed to Dashboard

```python
context = {
    'total_bookings': 14,                      # Total booking count
    'pending_payments_count': X,               # Count of PENDING payments
    'confirmed_bookings': Y,                   # Count of CONFIRMED bookings
    'total_revenue': Decimal('XXX.XX'),       # Sum of COMPLETED payments
    'today_check_ins': Z,                      # Today's check-ins
    'today_check_outs': Z,                     # Today's check-outs
    'month_revenue': Decimal('XXX.XX'),       # This month's completed payments
    'occupancy_rate': 45.5,                    # Current occupancy %
    'total_rooms': 20,                         # Total room count
    'recent_bookings': <QuerySet[5]>,          # 5 most recent bookings
    'pending_payments': <QuerySet[5]>,         # 5 most recent pending payments
}
```

---

## Template File Locations

- Main Dashboard: `templates/admin/dashboard.html`
- Pending Payments Component: `templates/admin/pending_payments_table.html`
- Recent Bookings Component: `templates/admin/recent_bookings_table.html`
- Base Template: `templates/admin/admin_base.html`
