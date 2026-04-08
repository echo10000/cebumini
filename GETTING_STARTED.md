# Getting Started with Cebu Hotel Management System

## 🚀 Quick Start (5 Minutes)

### Step 1: Verify Installation
```bash
cd c:\Users\Admin\Downloads\cebuhotel
python manage.py --version  # Should show Django 4.2.x
```

### Step 2: Run Migrations
```bash
python manage.py migrate
```

### Step 3: Create Admin User
```bash
python manage.py createsuperuser
# Follow prompts to create username and password
```

### Step 4: Start Development Server
```bash
python manage.py runserver
```

### Step 5: Access the Application
- **Home Page**: http://localhost:8000/
- **Login**: http://localhost:8000/auth/login/
- **Admin Panel**: http://localhost:8000/admin/
- **Dashboard**: http://localhost:8000/dashboard/ (after admin login)

---

## 📖 Feature Overview

### For Guests

#### 1. Registration & Login
1. Click "Sign Up" on home page
2. Fill in username, email, password
3. Login with credentials
4. Accept terms & conditions on first visit

#### 2. Browse Rooms
1. Navigate to "Rooms" section
2. View room details and images
3. Filter by type, price, capacity
4. Use pagination to browse

#### 3. Create Booking
1. Select a room
2. Choose check-in and check-out dates
3. System calculates total price automatically
4. Review booking details
5. Confirm booking
6. Booking confirmation displayed

#### 4. Manage Bookings
1. Go to "My Bookings"
2. View all your bookings
3. Cancel future bookings (click "Cancel")
4. View past booking history

### For Admins

#### 1. Dashboard Overview
1. Login as admin
2. Click "Admin" dropdown → "Dashboard"
3. View all key metrics at a glance
4. See recent bookings and room performance

#### 2. Room Management
1. Go to "Manage Rooms" section
2. View all rooms
3. Create new room (click "Add Room")
4. Edit room details
5. Delete rooms
6. Upload/manage images

#### 3. Booking Management
1. Click "Admin" → "All Bookings"
2. View all bookings in system
3. Filter by status, room, date
4. Confirm pending bookings
5. Cancel bookings if needed
6. View detailed booking information

#### 4. Analytics
1. **Main Dashboard** (`/dashboard/`)
   - View all metrics
   - See recent activity
   - Quick access to detailed analytics

2. **Revenue Analytics** (`/dashboard/revenue/`)
   - Track total revenue
   - See daily revenue chart
   - Analyze by room type
   - View trends

3. **Occupancy Analytics** (`/dashboard/occupancy/`)
   - Monitor occupancy rates
   - See room status
   - View daily trends
   - Compare by room type

4. **Booking Analytics** (`/dashboard/bookings/`)
   - Analyze booking patterns
   - See status distribution
   - View booking trends
   - Weekly patterns

---

## 🔑 Key Features Explained

### Booking System

**Overlap Prevention**
- System automatically prevents booking same room for overlapping dates
- Ensures no double-bookings

**Price Calculation**
- Automatically calculates: Number of nights × Price per night
- Shows total before confirmation

**Booking Statuses**
- **PENDING**: Awaiting admin confirmation
- **CONFIRMED**: Approved and active
- **CANCELLED**: Cancelled by user or admin

**Cancellation Rules**
- Guests can cancel future bookings only
- Admins can cancel any booking
- Cancellation requires reason

### Analytics

**Real-Time Metrics**
- Updates based on current bookings
- Shows today's check-ins/check-outs
- Displays available rooms

**Historical Trends**
- Last 30 days of data
- Daily, weekly, monthly summaries
- Trend indicators (up/down)

**Room Analytics**
- Performance per room type
- Most/least booked rooms
- Revenue contribution

---

## 📊 Dashboard Metrics Explained

### Primary Metrics

**Total Bookings**
- Count of all bookings (all statuses)
- Shows confirmed count separately

**Total Revenue**
- Sum of all confirmed bookings
- In Philippine Pesos (₱)

**Occupancy Rate**
- Percentage of rooms currently occupied
- Calculated from today's check-ins/outs

**Available Rooms**
- Count of rooms not currently booked
- Out of total rooms

### Secondary Metrics

**This Week's Stats**
- Bookings created this week
- Revenue from this week

**Today's Check-ins/Check-outs**
- Number of guests checking in today
- Number of guests checking out today

**Most Booked Room**
- Room with highest booking count
- Shows room type

---

## 🔧 Common Tasks

### Add a New Room

1. Login as admin
2. Go to Rooms → Create Room
3. Fill in:
   - Room Number (e.g., 101)
   - Room Type (Standard/Deluxe/Suite)
   - Description
   - Price per night
   - Capacity (max guests)
   - Amenities
4. Click "Create"
5. Upload room images
6. Room is ready for bookings

### Process a Booking

1. Go to "Admin" → "All Bookings"
2. Find PENDING booking
3. Click "Confirm" button
4. Review booking details
5. Click "Confirm Booking"
6. Status changes to CONFIRMED
7. Guest can check in

### Update Terms & Conditions

1. Go to Django Admin (/admin/)
2. Find Terms & Conditions section
3. Click "Add"
4. Enter new version number
5. Enter content (HTML/text)
6. Save
7. Users must re-accept on next login

---

## 🐛 Troubleshooting

### Issue: "Page not found"
**Solution**: Check URL routing
- Make sure you're on correct URL
- Check that migrations were run
- Verify apps are installed in INSTALLED_APPS

### Issue: "Admin access required"
**Solution**: Login as admin
- Create superuser: `python manage.py createsuperuser`
- Login through /auth/login/
- Verify role is set to ADMIN

### Issue: "Database error"
**Solution**: Run migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Issue: Charts not showing
**Solution**: Check Chart.js CDN
- Open browser console (F12)
- Check for JavaScript errors
- Verify internet connection (CDN access)

### Issue: "Overlap detected" when booking
**Solution**: This is expected
- Choose different dates
- Or choose different room
- System prevents double-bookings

---

## 📱 Using on Mobile

All features are mobile-responsive:

### Mobile Navigation
- Hamburger menu for small screens
- Touch-friendly buttons
- Responsive tables
- Optimized forms

### Mobile Features
- Browse rooms on phone
- Create bookings on phone
- View analytics on tablet
- Access admin dashboard

---

## 🔐 Security Tips

### For Guests
- Use strong passwords (8+ chars, mixed case, numbers)
- Don't share login credentials
- Verify email for password recovery
- Log out when done

### For Admins
- Change default password immediately
- Use complex admin password
- Don't share superuser credentials
- Log out of admin panel
- Review access logs regularly

---

## 📞 Support

### Error Messages

**"Check-in date must be before check-out date"**
- Make sure check-in < check-out
- Both dates must be in future

**"No available rooms for these dates"**
- All rooms booked for selected dates
- Choose different dates
- Choose different room type

**"This room is not available"**
- Room not available for booking
- Room might be under maintenance
- Try different room

**"Terms must be accepted"**
- Accept terms on first login
- Go to Terms page if needed
- Accept to continue

---

## 🎯 Typical Day in Hotel

### 7:00 AM - Check Admin Dashboard
1. Login to /dashboard/
2. View today's check-ins
3. View today's check-outs
4. Check occupancy rate

### 9:00 AM - Process Check-ins
1. Go to "All Bookings"
2. Find today's CONFIRMED bookings
3. Process guest check-in
4. Room marked as occupied

### 12:00 PM - Review Bookings
1. Check pending bookings
2. Confirm bookings from previous day
3. Process cancellations if any

### 3:00 PM - Check Revenue
1. Go to "Revenue Analytics"
2. Check today's revenue
3. View 30-day trends
4. Analyze room performance

### 5:00 PM - Process Check-outs
1. Identify checkout guests
2. Process check-outs
3. Prepare rooms for next guests
4. Verify room status

### 6:00 PM - View Occupancy
1. Check "Occupancy Analytics"
2. See which rooms are occupied
3. Plan for tomorrow
4. Check upcoming bookings

---

## 📈 Analytics Deep Dive

### Revenue Analytics
- **Line Chart**: Daily revenue over 30 days
- **Room Type Table**: Revenue breakdown by type
- **Weekly Summary**: Compare weeks
- **Monthly Summary**: Compare months

### Occupancy Analytics
- **Line Chart**: Daily occupancy % over 30 days
- **Room Status**: Visual cards for each room
- **By Room Type**: Occupancy per type
- **Trends**: Weekly and monthly comparison

### Booking Analytics
- **Pie Chart**: Status distribution (Confirmed/Pending/Cancelled)
- **Bar Chart**: Daily bookings over 30 days
- **Weekly Pattern**: Bookings by day of week
- **Monthly Comparison**: This vs last month

---

## 🎓 Best Practices

### For Best Results

1. **Regular Data Review**
   - Check dashboard daily
   - Monitor trends weekly
   - Analyze monthly performance

2. **Proactive Management**
   - Confirm bookings promptly
   - Update room availability
   - Manage T&C versions

3. **System Maintenance**
   - Review bookings regularly
   - Archive old data periodically
   - Monitor database size

4. **Guest Experience**
   - Make room info clear
   - Confirm bookings quickly
   - Provide quick support

---

## 📚 Learning Resources

### Built-in Documentation
- See DASHBOARD_GUIDE.md for analytics details
- See BOOKING_GUIDE.md for booking system details
- See COMPLETE_IMPLEMENTATION_SUMMARY.md for full project info

### Key Files to Review
- authentication/models.py - Database structure
- authentication/views_dashboard.py - Analytics logic
- templates/dashboard/ - Dashboard templates

---

## ✅ Verification Checklist

After setup, verify these work:

- [ ] Can register new user account
- [ ] Can login with credentials
- [ ] Can accept terms & conditions
- [ ] Can browse rooms
- [ ] Can create booking
- [ ] Can see booking confirmation
- [ ] Can view "My Bookings"
- [ ] Can cancel future booking
- [ ] Can login as admin
- [ ] Can view dashboard
- [ ] Can see metrics on dashboard
- [ ] Can view revenue analytics
- [ ] Can view occupancy analytics
- [ ] Can view booking analytics
- [ ] Can access room management
- [ ] Can access booking management
- [ ] Charts display correctly
- [ ] Mobile view works
- [ ] All links work correctly

---

## 🚀 Next Steps

1. **First Time Use**
   - Create admin account
   - Add some sample rooms
   - Create test bookings
   - Explore analytics

2. **Customization**
   - Update hotel information
   - Adjust room types/prices
   - Modify T&C
   - Customize templates

3. **Production Setup**
   - Configure proper database
   - Set up static file serving
   - Configure email
   - Set up SSL/HTTPS
   - Deploy to server

4. **Marketing**
   - Set up booking website
   - Configure payment gateway
   - Set up email notifications
   - Create booking flow

---

**Welcome to Cebu Hotel Management System!**

For questions or issues, refer to the comprehensive documentation files or review the code comments.

Happy hotel management! 🏨
