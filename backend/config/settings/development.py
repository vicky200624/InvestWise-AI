from .base import *
from corsheaders.defaults import default_headers

DEBUG = True

# Resolved CORS Policy Blocking Frontend Requests
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://investwiseai.duckdns.org",
    "http://investwiseai.duckdns.org:8000",
]

# Added DuckDNS domain and EC2 IP for external access
ALLOWED_HOSTS = [
    'localhost', 
    '127.0.0.1', 
    '0.0.0.0', 
    'testserver', 
    '54.87.205.228',
    'investwiseai.duckdns.org',
    '*'  # Note: '*' allows all traffic, which is fine for testing but can be removed for strict security later
]

CORS_ALLOW_ALL_ORIGINS = False

# Allow the custom header your frontend is sending to pass preflight checks
CORS_ALLOW_HEADERS = list(default_headers) + [
    "x-api-version",
]

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Only append the new Agentic AI app here (do not re-add ai_operations)
INSTALLED_APPS += [
    'apps.agentic_ai.apps.AgenticAiConfig',
]