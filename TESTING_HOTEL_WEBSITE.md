# Quick Start Guide - Hotel Website Testing

## Step 1: Clear Cache and Restart Server
```bash
# Stop current server (press Ctrl+C)
# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Start fresh
python manage.py runserver
```

## Step 2: Access the Website
Open your browser and navigate to:
```
http://localhost:8000/
```

## Step 3: What You Should See

### Homepage (Hero Section)
- Large "Luxury Awaits" headline
- Subtitle: "Experience unparalleled elegance..."
- Beautiful booking search bar with check-in, check-out, guests
- Smooth animations and dark gradient background

### Navigation Bar
- Fixed at top
- Becomes solid visible when scrolling
- Color matches hotel branding
- User authentication buttons (Login/Signup or Dashboard/Logout)

### Rooms Section
- Three featured room cards
- Deluxe Room ($199/night)
- Executive Suite ($349/night)
- Junior Suite ($279/night)
- Hover effects showing amenity icons
- "Book Now" buttons linking to rooms list

### Amenities Section
- 4 amenities with emoji icons:
  - 🏊 Olympic Pool
  - 🧖 Serenity Spa
  - 🍽️ Fine Dining
  - 💪 Fitness Center
- Cards have hover animations

### Contact Section
- Address display
- Phone number
- Email address

### Footer
- Social media links
- Quick navigation links
- User account section
- Service links
- Copyright notice

## Step 4: Test Key Features

### Responsive Design
1. Open DevTools (F12)
2. Click device toggles (tablet/mobile)
3. Verify all sections adapt properly

### Sticky Navigation
1. Scroll down the page
2. Watch nav background change from transparent to solid
3. Links remain accessible

### Smooth Scrolling
1. Click any anchor link (e.g., "Rooms")
2. Page smoothly scrolls to section

### "Book Now" Buttons
1. Click a room's "Book Now" button
2. Should redirect to rooms list page
3. Verify proper URL: `/rooms/`

### Authentication Links (Not Logged In)
- Click "Login" → goes to login page
- Click "Sign Up" → goes to signup page
- Click "Book Now" button → search bar appears

### Authentication Links (Logged In)
- Click "Dashboard" → user dashboard
- Click "Logout" → logs out user

## Step 5: Verify No Errors

### Django Console
Check for these errors:
- ✅ No 404 errors for static files
- ✅ No reverse URL errors
- ✅ No template rendering errors

### Browser Console (F12)
- ✅ No JavaScript errors
- ✅ No 404 requests
- ✅ All fonts load properly

## Step 6: Test Mobile View

### Using DevTools
1. Press F12
2. Toggle device toolbar (Ctrl+Shift+M)
3. Test on:
   - iPhone 12
   - iPad
   - Android devices

### What to Check
- ✅ Navigation collapses properly
- ✅ Buttons are touch-friendly
- ✅ Text is readable
- ✅ Images scale correctly
- ✅ Forms are usable

## Troubleshooting During Testing

### If you see "Page not found (404)"
```bash
# Restart server and clear cache
python manage.py runserver --clear-cache
```

### If URLs don't work (NoReverseMatch)
```bash
# Check that URLs are fixed
grep "rooms:list" templates/hotel_landing.html
grep "rooms:list" templates/bookings/booking_history.html
grep "rooms:list" templates/recommendations/user_profile.html
```

### If styling looks wrong
```bash
# Collect static files
python manage.py collectstatic --noinput

# Hard refresh page (Ctrl+Shift+R on Windows/Linux, Cmd+Shift+R on Mac)
```

### If fonts aren't loading
- Check browser console
- Verify internet connection (fonts load from CDN)
- Try a different browser

## Quick Feature Testing Checklist

**Homepage Features**
- [ ] Hero section displays properly
- [ ] Booking bar shows all date/guest fields
- [ ] Navigation bar is sticky and changes on scroll
- [ ] Three room cards display with prices
- [ ] Hover effects work on cards
- [ ] Amenities section shows 4 items
- [ ] Contact information is visible
- [ ] Footer shows all links

**User Authentication**
- [ ] Not logged in: shows "Login" and "Sign Up"
- [ ] After login: shows "Dashboard" and "Logout"
- [ ] Authentication links navigate correctly

**Mobile Responsiveness**
- [ ] Navigation adapts to mobile
- [ ] Grid layouts stack properly
- [ ] Text remains readable
- [ ] Buttons are larger on mobile
- [ ] Footer reorganizes for mobile

**Links and Navigation**
- [ ] "Book Now" buttons work
- [ ] Navigation links scroll smoothly
- [ ] Social icons are visible
- [ ] All footer links navigate properly

## Performance Notes

- Page should load in < 2 seconds
- Animations should be smooth (60fps)
- No layout shifts after page loads
- Images load from inline SVG (no network delay)

## Next Steps After Testing

1. ✅ If everything works, the website is ready!
2. ✅ Test on actual mobile devices
3. ✅ Share with stakeholders
4. ✅ Gather feedback
5. ✅ Move to production deployment

---

**Happy Testing! 🎉**

If any issues occur, refer to: `HOTEL_WEBSITE_IMPLEMENTATION.md`
