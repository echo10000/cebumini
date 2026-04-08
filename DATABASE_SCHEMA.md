# Database Schema & Migrations

## Overview
After running migrations, your Django database will have these tables for the authentication system.

## Tables Structure

### 1. terms_and_conditions
Stores all Terms & Conditions versions

```
┌─────────────────────────────────────────┐
│    terms_and_conditions                 │
├─────────────────────────────────────────┤
│ id (PK, AutoField)                      │
│ version (VARCHAR, max_length=20)        │ ← "1.0", "2.0", etc
│ content (LONGTEXT)                      │ ← Full T&C text
│ is_active (BOOLEAN)                     │ ← Current active version
│ created_at (DATETIME)                   │ ← Auto-generated
│ updated_at (DATETIME)                   │ ← Auto-updated
└─────────────────────────────────────────┘
```

### 2. users (CustomUser)
Stores user information with T&C tracking

```
┌────────────────────────────────────────────────┐
│          users (CustomUser)                    │
├────────────────────────────────────────────────┤
│ id (PK, AutoField)                             │
│ password (VARCHAR, max_length=128)             │
│ last_login (DATETIME, NULL)                    │
│ is_superuser (BOOLEAN)                         │
│ username (VARCHAR, max_length=150, UNIQUE)    │
│ first_name (VARCHAR, max_length=30)           │
│ last_name (VARCHAR, max_length=30)            │
│ email (VARCHAR, max_length=254, UNIQUE)       │
│ is_staff (BOOLEAN)                            │
│ is_active (BOOLEAN)                           │
│ date_joined (DATETIME)                        │
│ role (VARCHAR, max_length=20)                 │ ← "GUEST" or "ADMIN"
│ phone_number (VARCHAR, NULL, max_length=20)  │
│ is_email_verified (BOOLEAN)                   │
│ terms_accepted (BOOLEAN)                      │ ← NEW: T&C status
│ terms_accepted_at (DATETIME, NULL)            │ ← NEW: Acceptance timestamp
│ terms_version (VARCHAR, NULL, max_length=20) │ ← NEW: Accepted version
│ created_at (DATETIME)                         │ ← Auto-generated
│ updated_at (DATETIME)                         │ ← Auto-updated
└────────────────────────────────────────────────┘
```

### 3. auth_group
Django's built-in groups table (auto-created)

```
┌─────────────────────────────────┐
│       auth_group                │
├─────────────────────────────────┤
│ id (PK)                         │
│ name (VARCHAR, UNIQUE)          │
└─────────────────────────────────┘
```

### 4. auth_permission
Django's built-in permissions (auto-created)

```
┌─────────────────────────────────────────┐
│      auth_permission                    │
├─────────────────────────────────────────┤
│ id (PK)                                 │
│ content_type_id (FK)                   │
│ codename (VARCHAR)                      │
│ name (VARCHAR)                          │
└─────────────────────────────────────────┘
```

## Key Fields Explained

### TermsAndConditions Model

| Field | Type | Purpose | Example |
|-------|------|---------|---------|
| `id` | AutoField | Primary key | 1, 2, 3... |
| `version` | CharField | Version identifier | "1.0", "2.0" |
| `content` | TextField | Full T&C text | "TERMS & CONDITIONS..." |
| `is_active` | Boolean | Current active version | True/False |
| `created_at` | DateTime | Creation timestamp | 2026-02-13 10:30:00 |
| `updated_at` | DateTime | Last update timestamp | 2026-02-13 11:45:00 |

### CustomUser Model (T&C Fields)

| Field | Type | Purpose | Example |
|-------|------|---------|---------|
| `terms_accepted` | Boolean | Has accepted T&C | True/False |
| `terms_accepted_at` | DateTime | When T&C was accepted | 2026-02-13 14:20:00 |
| `terms_version` | CharField | Which version accepted | "1.0" |

## Relationships

### Many-to-Many: User ←→ TermsAndConditions

**Implicit relationship through tracking fields:**

```
One TermsAndConditions version (e.g., "1.0")
    ↓
Many users can accept the same version
    ↓
Each user tracks: terms_accepted, terms_accepted_at, terms_version
```

**Query Examples:**

```python
# Get all users who accepted T&C v1.0
CustomUser.objects.filter(terms_version='1.0', terms_accepted=True)

# Get all active T&C
TermsAndConditions.objects.filter(is_active=True)

# Get latest T&C version
latest_tac = TermsAndConditions.objects.latest('created_at')
```

## Migration Files

When you run `python manage.py makemigrations`, Django creates migration files:

```
authentication/migrations/
├── __init__.py
├── 0001_initial.py          ← Creates CustomUser model
├── 0002_*.py                 ← Adds T&C fields to CustomUser
└── 0003_termandconditions.py ← Creates TermsAndConditions model
```

## SQL Schema (SQLite Example)

```sql
-- TermsAndConditions table
CREATE TABLE "terms_and_conditions" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "version" varchar(20) NOT NULL,
    "content" text NOT NULL,
    "is_active" boolean NOT NULL,
    "created_at" datetime NOT NULL,
    "updated_at" datetime NOT NULL
);

-- Users table (CustomUser)
CREATE TABLE "users" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "password" varchar(128) NOT NULL,
    "last_login" datetime NULL,
    "is_superuser" boolean NOT NULL,
    "username" varchar(150) NOT NULL UNIQUE,
    "first_name" varchar(30) NOT NULL,
    "last_name" varchar(30) NOT NULL,
    "email" varchar(254) NOT NULL UNIQUE,
    "is_staff" boolean NOT NULL,
    "is_active" boolean NOT NULL,
    "date_joined" datetime NOT NULL,
    "role" varchar(20) NOT NULL DEFAULT 'GUEST',
    "phone_number" varchar(20) NULL,
    "is_email_verified" boolean NOT NULL DEFAULT False,
    "terms_accepted" boolean NOT NULL DEFAULT False,
    "terms_accepted_at" datetime NULL,
    "terms_version" varchar(20) NULL,
    "created_at" datetime NOT NULL,
    "updated_at" datetime NOT NULL
);
```

## Index Information

Django automatically creates indexes on:
- All Primary Keys
- All Foreign Keys
- `username` (UNIQUE)
- `email` (UNIQUE)
- `version` (in terms_and_conditions, for lookups)

## Data Flow

### Registration Flow
```
User submits registration form with T&C checkbox
    ↓
Form validates and creates user
    ↓
INSERT INTO users (username, email, ..., terms_accepted, terms_accepted_at, terms_version)
    ↓
values (..., True, NOW(), '1.0')
```

### Login + T&C Flow
```
User logs in
    ↓
SELECT terms_accepted FROM users WHERE username=?
    ↓
If False: Redirect to accept page
    ↓
User submits acceptance
    ↓
UPDATE users SET terms_accepted=True, terms_accepted_at=NOW(), terms_version='1.0'
```

### Dashboard Protection
```
User accesses /dashboard/
    ↓
SELECT terms_accepted FROM users WHERE id=?
    ↓
If False: Redirect to accept page
If True: Show dashboard
```

## Backup & Restore

### Export current state
```bash
python manage.py dumpdata authentication > auth_backup.json
```

### Restore from backup
```bash
python manage.py loaddata auth_backup.json
```

### Export specific data
```bash
# Export only users
python manage.py dumpdata authentication.CustomUser > users_backup.json

# Export only T&C
python manage.py dumpdata authentication.TermsAndConditions > terms_backup.json
```

## Database Queries for Management

### Check T&C acceptance statistics
```python
from django.db.models import Count
from authentication.models import CustomUser

# Count by acceptance status
CustomUser.objects.values('terms_accepted').annotate(count=Count('id'))
# Output: [{'terms_accepted': True, 'count': 25}, {'terms_accepted': False, 'count': 3}]

# Count by version
CustomUser.objects.filter(terms_accepted=True).values('terms_version').annotate(count=Count('id'))
# Output: [{'terms_version': '1.0', 'count': 25}]
```

### Find users who haven't accepted
```python
from authentication.models import CustomUser

users = CustomUser.objects.filter(terms_accepted=False)
for user in users:
    print(f"{user.username} - {user.email}")
```

### Recent acceptances
```python
from authentication.models import CustomUser
from django.utils import timezone
from datetime import timedelta

# Last 7 days
recent = CustomUser.objects.filter(
    terms_accepted_at__gte=timezone.now() - timedelta(days=7)
)

# By hour
for user in recent:
    print(f"{user.username} accepted at {user.terms_accepted_at}")
```

## Performance Considerations

- **Indexes**: Primary keys and unique fields already indexed
- **Query Optimization**: Use `select_related()` if needed for joins
- **Pagination**: Implement for large user lists
- **Archive Old Versions**: Keep latest 5 T&C versions, archive older

```python
# Archive old T&C versions
from authentication.models import TermsAndConditions

old_versions = TermsAndConditions.objects.filter(
    is_active=False
).order_by('-created_at')[5:]

# Optionally delete or mark for archival
for version in old_versions:
    version.delete()  # Or archive to separate table
```

## Troubleshooting

### Check migration status
```bash
python manage.py showmigrations authentication
```

### Rollback migrations
```bash
# Go back one migration
python manage.py migrate authentication 0002_previous_migration

# Go to initial state
python manage.py migrate authentication zero
```

### Check database integrity
```bash
python manage.py dbshell
```

Then in SQLite:
```sql
-- Check for orphaned records
SELECT COUNT(*) FROM users WHERE terms_accepted = True AND terms_accepted_at IS NULL;

-- Check data consistency
SELECT version, COUNT(*) as user_count 
FROM users 
WHERE terms_version IS NOT NULL 
GROUP BY version;
```

---

**Database Status**: ✅ Production Ready
**Backup Strategy**: ✅ Use dumpdata/loaddata
**Scaling**: ✅ Add database replication for high volume
