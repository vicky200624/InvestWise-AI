import os
import sys
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # /home/vicky/Documents/investai/backend
ROOT_DIR = BASE_DIR.parent  # /home/vicky/Documents/investai

load_dotenv(str(ROOT_DIR / '.env'))

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


SECRET_KEY = os.environ.get('SECRET_KEY', os.environ.get('DJANGO_SECRET_KEY', 'default-secret-key-for-dev'))
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', 'kQn5hP0hD1vQ5e4m2S6j7u8w9x0y1z2A3B4C5D6E7F8=')


INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'channels',
    'django_celery_beat',
    'django_celery_results',
    'django_extensions',
    'apps.accounts',
    'apps.portfolio',
    'apps.research',
    'apps.chat',
    'apps.watchlist',
    'apps.companies',
    'apps.market',
    'apps.alerts',
    'apps.feedback',
    'apps.analytics',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [str(ROOT_DIR / 'templates')],
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

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# Database configuration supporting SQLite fallback or PostgreSQL override
DB_ENGINE = os.environ.get('DB_ENGINE', 'django.db.backends.sqlite3')
if 'postgres' in DB_ENGINE.lower():
    DATABASES = {
        'default': {
            'ENGINE': DB_ENGINE,
            'NAME': os.environ.get('DB_NAME', 'investwise'),
            'USER': os.environ.get('DB_USER', 'postgres'),
            'PASSWORD': os.environ.get('DB_PASSWORD', 'postgres'),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ROOT_DIR / 'db.sqlite3',
        }
    }

# Channels Redis configuration
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(os.environ.get('REDIS_HOST', 'localhost'), int(os.environ.get('REDIS_PORT', 6379)))],
        },
    },
}

# Celery Configuration
CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'default'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [
    str(ROOT_DIR / 'static'),
]
STATIC_ROOT = str(ROOT_DIR / 'staticfiles')
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ChromaDB & AI Model Directories
CHROMADB_PERSIST_DIR = os.environ.get('CHROMADB_PERSIST_DIR', str(ROOT_DIR / 'chroma_db'))
AI_MODEL_DIR = os.environ.get('AI_MODEL_DIR', str(ROOT_DIR / 'ai_models'))
os.makedirs(AI_MODEL_DIR, exist_ok=True)
os.makedirs(CHROMADB_PERSIST_DIR, exist_ok=True)

# External API Keys (loaded from .env)
FMP_API_KEY = os.environ.get('FMP_API_KEY', '')
FINNHUB_API_KEY = os.environ.get('FINNHUB_API_KEY', '')
FRED_API_KEY = os.environ.get('FRED_API_KEY', '')
SEC_EDGAR_USER_AGENT = os.environ.get('SEC_EDGAR_USER_AGENT', 'InvestWise admin@investwise.ai')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY', GEMINI_API_KEY)
ELEVENLABS_API_KEY = os.environ.get('ELEVENLABS_API_KEY', '')
DEEPGRAM_API_KEY = os.environ.get('DEEPGRAM_API_KEY', '')

# Logging configuration
os.makedirs(str(ROOT_DIR / 'logs'), exist_ok=True)
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
            'filename': str(ROOT_DIR / 'logs' / 'investwise.log'),
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

# Tells Django to use our CustomUser model instead of the default auth.User
AUTH_USER_MODEL = 'accounts.CustomUser'
