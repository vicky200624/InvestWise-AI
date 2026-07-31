"""
InvestWise AI 3.0 — Django Settings

Production-ready configuration for the Agentic AI investment platform.
Integrates: PostgreSQL, Celery/Redis, Django Channels, ChromaDB, and ML model storage.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# ==============================================================================
# PATH CONFIGURATION
# ==============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(BASE_DIR, '.env'))

# ==============================================================================
# SECURITY
# ==============================================================================
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-s$xi04h*iaiww%gxu8f741fl8hh*#5kttmwgvd=5roxt)m$luq'
)

DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = ['*'] if DEBUG else os.environ.get('ALLOWED_HOSTS', '').split(',')

# ==============================================================================
# APPLICATION DEFINITION
# ==============================================================================
INSTALLED_APPS = [
    # Django Channels (must be before django.contrib.staticfiles for ASGI)
    'daphne',

    # Django Core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-Party
    'rest_framework',
    'corsheaders',
    'channels',
    'django_celery_beat',
    'django_celery_results',

    # InvestWise Application
    'investwise',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'investwise_core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ==============================================================================
# ASGI / WSGI
# ==============================================================================
ASGI_APPLICATION = 'investwise_core.asgi.application'
WSGI_APPLICATION = 'investwise_core.wsgi.application'

# ==============================================================================
# DATABASE — PostgreSQL (required for LangGraph PostgresSaver)
# Falls back to MySQL if POSTGRES_DB is not set (migration period).
# ==============================================================================
if os.environ.get('POSTGRES_DB'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('POSTGRES_DB', 'investwise_db'),
            'USER': os.environ.get('POSTGRES_USER', 'investwise_user'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD', ''),
            'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
            'PORT': os.environ.get('POSTGRES_PORT', '5432'),
            'OPTIONS': {
                'connect_timeout': 10,
            },
        }
    }
else:
    # Fallback: MySQL (existing database during migration period)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'investwise_db',
            'USER': 'investwise_user',
            'PASSWORD': os.environ.get('INVESTWISE_DB_PASS'),
            'HOST': 'localhost',
            'PORT': '3306',
            'OPTIONS': {
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }

# ==============================================================================
# DJANGO CHANNELS — Redis Channel Layer
# ==============================================================================
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [(
                os.environ.get('REDIS_HOST', 'localhost'),
                int(os.environ.get('REDIS_PORT', 6379))
            )],
            # Allow larger messages for streaming AI agent output
            'capacity': 1500,
            'expiry': 60,
        },
    },
}

# ==============================================================================
# CELERY — Async Task Queue Configuration
# ==============================================================================
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# Production tuning for long-running AI agent tasks:
CELERY_TASK_ACKS_LATE = True                    # Ack after completion (crash-safe)
CELERY_WORKER_PREFETCH_MULTIPLIER = 1           # Don't prefetch (prevents blocking)
CELERY_TASK_SOFT_TIME_LIMIT = 300               # 5-minute soft limit
CELERY_TASK_TIME_LIMIT = 600                    # 10-minute hard limit
CELERY_TASK_RETRY_BACKOFF = True                # Exponential backoff on retries
CELERY_TASK_RETRY_BACKOFF_MAX = 600             # Max 10-minute backoff

# Store task results in Django DB for admin visibility
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'django-cache'

# Periodic task scheduling (Celery Beat)
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# ==============================================================================
# REST FRAMEWORK
# ==============================================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# ==============================================================================
# CORS
# ==============================================================================
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = [] if DEBUG else os.environ.get('CORS_ORIGINS', '').split(',')

# ==============================================================================
# PASSWORD VALIDATION
# ==============================================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ==============================================================================
# INTERNATIONALIZATION
# ==============================================================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ==============================================================================
# STATIC FILES
# ==============================================================================
STATIC_URL = 'static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# ==============================================================================
# LOGIN / AUTH REDIRECTS
# ==============================================================================
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'

# ==============================================================================
# DEFAULT PRIMARY KEY
# ==============================================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==============================================================================
# INVESTWISE AI 3.0 — CUSTOM SETTINGS
# ==============================================================================

# ChromaDB persistent storage for RAG document embeddings
CHROMADB_PERSIST_DIR = os.path.join(BASE_DIR, 'chroma_db')

# Trained ML model artifacts directory
AI_MODEL_DIR = os.path.join(BASE_DIR, 'ai_models')
os.makedirs(AI_MODEL_DIR, exist_ok=True)

# External API Keys (loaded from .env)
FMP_API_KEY = os.environ.get('FMP_API_KEY', '')
FINNHUB_API_KEY = os.environ.get('FINNHUB_API_KEY', '')
FRED_API_KEY = os.environ.get('FRED_API_KEY', '')
SEC_EDGAR_USER_AGENT = os.environ.get('SEC_EDGAR_USER_AGENT', 'InvestWise admin@investwise.ai')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

# ==============================================================================
# LOGGING
# ==============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'investwise.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'investwise': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'celery': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}