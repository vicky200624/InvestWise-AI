from .base import *
import os

DEBUG = False

ENV = 'production'

allowed_hosts_env = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1')
ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_env.split(',') if host.strip()]

cors_env = os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost,http://127.0.0.1,https://investwise.ai')
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in cors_env.split(',') if origin.strip()]

# Security hardening for production
SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', 31536000))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True').lower() in ('true', '1', 'yes')
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')

# Optional PostgreSQL setup if DATABASE_URL is provided, 
# else it falls back to sqlite from base.py
import dj_database_url
db_url = os.environ.get('DATABASE_URL')
if db_url:
    DATABASES['default'] = dj_database_url.config(default=db_url)

# Production-specific settings
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (
    'rest_framework.renderers.JSONRenderer',
)

# Disable browsable API in production
REST_FRAMEWORK.pop('DEFAULT_SCHEMA_CLASS', None)

# Enforce strong password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Session security
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_SAVE_EVERY_REQUEST = True

# JWT security
SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] = timedelta(minutes=30)  # Shorter for production
SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'] = timedelta(days=1)
SIMPLE_JWT['ROTATE_REFRESH_TOKENS'] = True
SIMPLE_JWT['BLACKLIST_AFTER_ROTATION'] = True

# Ensure HTTPS in production
CSRF_COOKIE_DOMAIN = os.environ.get('CSRF_COOKIE_DOMAIN', None)
SESSION_COOKIE_DOMAIN = os.environ.get('SESSION_COOKIE_DOMAIN', None)