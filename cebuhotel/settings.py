"""
Django settings for cebuhotel project.
"""
import os
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-your-secret-key-change-this-in-production'

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'django_otp',
    'django_otp.plugins.otp_totp',
    'qrcode',
    'authentication',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'authentication.middleware.CurrentRequestMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'cebuhotel.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'authentication.context_processors.guest_notifications',
                'authentication.context_processors.echo_chatbot_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'cebuhotel.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# Media Files Configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'authentication.CustomUser'

# Session Configuration
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_SAVE_EVERY_REQUEST = True

# Redirect URLs
LOGIN_URL = 'auth:login'
LOGIN_REDIRECT_URL = 'auth:dashboard'
LOGOUT_REDIRECT_URL = 'auth:login'

# Django Sites Framework
SITE_ID = 1

# OAuth2 Configuration
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Email Configuration - Gmail SMTP
# Send real emails via Gmail
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'echogoodkid@gmail.com'
EMAIL_HOST_PASSWORD = 'kmfakmtmpwditwtc'  # App password (spaces removed for clarity)
DEFAULT_FROM_EMAIL = 'Cebu Hotel <echogoodkid@gmail.com>'
EMAIL_TIMEOUT = 10
SERVER_EMAIL = 'Cebu Hotel <echogoodkid@gmail.com>'

# Allauth Settings
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_ADAPTER = 'authentication.adapters.CustomAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'authentication.adapters.CustomSocialAccountAdapter'
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'FIELDS': [
            'email',
            'first_name',
            'last_name',
            'picture',
        ]
    }
}
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_QUERY_EMAIL = True
SOCIALACCOUNT_STORE_TOKENS = True

# Disable allauth messages (no success message on login/signup)
ACCOUNT_LOGIN_MESSAGE_LEVEL = False
SOCIALACCOUNT_LOGIN_MESSAGE_LEVEL = False
OTP_TOTP_ISSUER = 'Cebu Hotel'
OTP_LOGIN_URL = '/auth/login/'

# 2FA Settings
TWO_FACTOR_ENABLED = True
TWO_FACTOR_REQUIRED = True
OTP_EMAIL_SENDER = 'noreply@cebu-luxury.com'
OTP_EMAIL_SUBJECT = 'Your Cebu Luxury Verification Code'
OTP_EMAIL_TOKEN_VALIDITY = 300  # 5 minutes
# ==================== PAYMENT CONFIGURATION ====================
# Stripe Test Keys (FREE TEST MODE)
STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY', 'pk_test_51234567890')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', 'sk_test_01234567890')

# PayMongo Test Keys (LOCAL PH PAYMENTS)
PAYMONGO_PUBLIC_KEY = config('PAYMONGO_PUBLIC_KEY', default='pk_test_xyz123456789')
PAYMONGO_SECRET_KEY = config('PAYMONGO_SECRET_KEY', default='sk_test_xyz123456789')
PAYMONGO_WEBHOOK_SECRET = config('PAYMONGO_WEBHOOK_SECRET', default='')
PAYMONGO_TEST_MODE = config('PAYMONGO_TEST_MODE', default=True, cast=bool)  # Set to False for production

# GCash Test Configuration
GCASH_MERCHANT_ID = os.getenv('GCASH_MERCHANT_ID', 'test_merchant_id')
GCASH_API_KEY = os.getenv('GCASH_API_KEY', 'test_api_key')
GCASH_TEST_MODE = True  # Set to False for production

# Payment Settings
PAYMENT_CURRENCY = 'PHP'
PAYMENT_TEST_MODE = True  # TEST MODE - Change to False for production
