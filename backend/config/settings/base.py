import os
import sys
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # /app/backend or repo backend dir
ROOT_DIR = BASE_DIR.parent

load_dotenv(str(ROOT_DIR / '.env'))

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def env_bool(name: str, default: bool = False) -> bool:
    """Parse environment variable as boolean."""
    return os.environ.get(name, str(default)).lower() in ('true', '1', 'yes', 'on')


def env_int(name: str, default: int) -> int:
    """Parse environment variable as integer with fallback."""
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


ENV = os.environ.get('DJANGO_ENV', 'development')

SECRET_KEY = os.environ.get(
    'SECRET_KEY', 
    os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-investwise-prod-secret-key-change-in-env-file')
)
ENCRYPTION_KEY = os.environ.get(
    'ENCRYPTION_KEY', 
    os.environ.get('DJANGO_ENCRYPTION_KEY', 'investwise_default_32_byte_key_123456')
)

if ENV == 'production' and SECRET_KEY == 'default-secret-key-for-dev':
    raise RuntimeError('In production, SECRET_KEY must be set via environment variable!')
if ENV == 'production' and ENCRYPTION_KEY == 'kQn5hP0hD1vQ5e4m2S6j7u8w9x0y1z2A3B4C5D6E7F8=':
    raise RuntimeError('In production, ENCRYPTION_KEY must be set via environment variable!')


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
    'apps.ai_operations',
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
    'core.middleware.SecurityHeadersMiddleware',
    'core.middleware.RequestLoggingMiddleware',
    'core.middleware.IPRateLimitMiddleware',
    'core.middleware.APIVersioningMiddleware',
]

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = env_bool('SECURE_BROWSER_XSS_FILTER', True)
X_FRAME_OPTIONS = os.environ.get('X_FRAME_OPTIONS', 'DENY')

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
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.ScopedRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': os.environ.get('THROTTLE_ANON_RATE', '60/min'),
        'user': os.environ.get('THROTTLE_USER_RATE', '600/min'),
        'auth': os.environ.get('THROTTLE_AUTH_RATE', '10/min'),
        'ai': os.environ.get('THROTTLE_AI_RATE', '20/min'),
    },
    'EXCEPTION_HANDLER': 'core.exceptions.custom_exception_handler',
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
}

# Extended JWT Token Lifetimes for Seamless Testing & Production
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# Database Configuration
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

# Channels Redis Configuration
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
] if (ROOT_DIR / 'static').exists() else []
STATIC_ROOT = str(ROOT_DIR / 'staticfiles')
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ChromaDB & AI Model Directories
CHROMADB_PERSIST_DIR = os.environ.get('CHROMADB_PERSIST_DIR', str(ROOT_DIR / 'chroma_db'))
AI_MODEL_DIR = os.environ.get('AI_MODEL_DIR', str(ROOT_DIR / 'ai_models'))
os.makedirs(AI_MODEL_DIR, exist_ok=True)
os.makedirs(CHROMADB_PERSIST_DIR, exist_ok=True)

# External API Keys
FMP_API_KEY = os.environ.get('FMP_API_KEY', '')
FINNHUB_API_KEY = os.environ.get('FINNHUB_API_KEY', '')
FRED_API_KEY = os.environ.get('FRED_API_KEY', '')
SEC_EDGAR_USER_AGENT = os.environ.get('SEC_EDGAR_USER_AGENT', 'InvestWise admin@investwise.ai')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY', GEMINI_API_KEY)
ELEVENLABS_API_KEY = os.environ.get('ELEVENLABS_API_KEY', '')
DEEPGRAM_API_KEY = os.environ.get('DEEPGRAM_API_KEY', '')

# Custom User Model
AUTH_USER_MODEL = 'accounts.CustomUser'

# Logging Configuration
os.makedirs(str(ROOT_DIR / 'logs'), exist_ok=True)
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO' if ENV == 'development' else 'WARNING')
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(ROOT_DIR / 'logs' / 'investwise.log'),
            'formatter': 'verbose',
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 5,
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(ROOT_DIR / 'logs' / 'investwise_errors.log'),
            'formatter': 'verbose',
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 5,
            'level': 'ERROR',
        },
    },
    'loggers': {
        'investwise': {
            'handlers': ['console', 'file', 'error_file'],
            'level': LOG_LEVEL,
            'propagate': True,
        },
        'celery': {
            'handlers': ['console', 'file', 'error_file'],
            'level': LOG_LEVEL,
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console', 'error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console', 'error_file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# Cache Configuration
USE_REDIS_CACHE = env_bool('USE_REDIS_CACHE', False)
if USE_REDIS_CACHE:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379/1'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            },
            'TIMEOUT': env_int('CACHE_TIMEOUT', 300),
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'investwise-cache',
            'TIMEOUT': env_int('CACHE_TIMEOUT', 300),
        }
    }