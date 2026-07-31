from django.db import models
from django.contrib.auth.models import User
from core.encryption import encrypt_value, decrypt_value

class UserPortfolio(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    total_invested = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    current_value = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    xirr = models.FloatField(default=0.0)
    last_synced = models.DateTimeField(null=True, blank=True)

class BrokerCredentials(models.Model):
    BROKER_CHOICES = [('ANGELONE', 'Angel One'), ('ZERODHA', 'Zerodha')]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='broker_credentials')
    broker_name = models.CharField(max_length=20, choices=BROKER_CHOICES, default='ANGELONE')
    _api_key = models.CharField(max_length=255, blank=True, default='', db_column='api_key')
    client_id = models.CharField(max_length=100, blank=True, default='')
    _pin = models.CharField(max_length=255, blank=True, default='', db_column='pin')
    _totp_secret = models.CharField(max_length=255, blank=True, default='', db_column='totp_secret')
    is_active = models.BooleanField(default=True)
    connected_at = models.DateTimeField(auto_now_add=True)

    @property
    def api_key(self):
        return decrypt_value(self._api_key)

    @api_key.setter
    def api_key(self, value):
        self._api_key = encrypt_value(value)

    @property
    def pin(self):
        return decrypt_value(self._pin)

    @pin.setter
    def pin(self, value):
        self._pin = encrypt_value(value)

    @property
    def totp_secret(self):
        return decrypt_value(self._totp_secret)

    @totp_secret.setter
    def totp_secret(self, value):
        self._totp_secret = encrypt_value(value)
