"""
Django settings for CHORD backend.
Configured for production deployment on Render / Railway with Supabase Managed PostgreSQL
and Vercel / Netlify frontend integration.
"""

from pathlib import Path
import os
import sys

# Optional: Load local .env file if python-dotenv is present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Optional: dj_database_url for PostgreSQL / Supabase connection pooling
try:
    import dj_database_url
except ImportError:
    dj_database_url = None

# Optional: whitenoise for production static file serving
try:
    import whitenoise
    HAS_WHITENOISE = True
except ImportError:
    HAS_WHITENOISE = False

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Security & Environment Config
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-chord-welfare-delivery-secret-key-prod-dev-change-in-prod'
)

DEBUG = os.environ.get('DEBUG', 'False').strip().lower() in ('true', '1', 'yes')

raw_allowed_hosts = os.environ.get('ALLOWED_HOSTS', '*')
if raw_allowed_hosts == '*':
    ALLOWED_HOSTS = ['*']
else:
    ALLOWED_HOSTS = [h.strip() for h in raw_allowed_hosts.split(',') if h.strip()]
    default_hosts = ['.onrender.com', '.railway.app', '.up.railway.app', '.vercel.app', 'localhost', '127.0.0.1']
    for host in default_hosts:
        if host not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(host)

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
]

if HAS_WHITENOISE:
    INSTALLED_APPS.append('whitenoise.runserver_nostatic')

INSTALLED_APPS.extend([
    'django.contrib.staticfiles',
    'api.apps.ApiConfig',
])

MIDDLEWARE = [
    'api.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
]

if HAS_WHITENOISE:
    MIDDLEWARE.append('whitenoise.middleware.WhiteNoiseMiddleware')

MIDDLEWARE.extend([
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
])

ROOT_URLCONF = 'chord_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR.parent],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'chord_backend.wsgi.application'

# Database Configuration (Supabase PostgreSQL / SQLite Fallback)
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL and dj_database_url:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = []

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
if HAS_WHITENOISE:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files (User uploads / documents)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS & CSRF Dynamic Whitelist Configuration
CORS_ALLOW_ALL_ORIGINS = os.environ.get('CORS_ALLOW_ALL_ORIGINS', 'True').strip().lower() in ('true', '1', 'yes')

raw_cors_origins = os.environ.get(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5500,http://localhost:8080,https://*.vercel.app,https://*.netlify.app'
)
CORS_ALLOWED_ORIGINS = [o.strip() for o in raw_cors_origins.split(',') if o.strip()]

raw_csrf_origins = os.environ.get(
    'CSRF_TRUSTED_ORIGINS',
    'http://localhost:3000,http://127.0.0.1:3000,https://*.vercel.app,https://*.onrender.com,https://*.netlify.app,https://*.railway.app,https://*.up.railway.app'
)
CSRF_TRUSTED_ORIGINS = [o.strip() for o in raw_csrf_origins.split(',') if o.strip()]
