import base64
import hashlib
from cryptography.fernet import Fernet
from django.conf import settings

def get_fernet():
    key = getattr(settings, 'ENCRYPTION_KEY', 'default-investwise-encryption-key')
    if not key:
        key = 'default-investwise-encryption-key'
    try:
        return Fernet(key.encode())
    except Exception:
        key_bytes = hashlib.sha256(key.encode()).digest()
        fernet_key = base64.urlsafe_b64encode(key_bytes)
        return Fernet(fernet_key)


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
