from cryptography.fernet import Fernet
from django.conf import settings

def get_fernet():
    key = getattr(settings, 'ENCRYPTION_KEY', None)
    if not key:
        raise Exception("ENCRYPTION_KEY not set in settings")
    return Fernet(key.encode())

def encrypt_value(value: str) -> str:
    if not value:
        return value
    f = get_fernet()
    return f.encrypt(value.encode()).decode()

def decrypt_value(value: str) -> str:
    if not value:
        return value
    f = get_fernet()
    try:
        return f.decrypt(value.encode()).decode()
    except Exception:
        return value
