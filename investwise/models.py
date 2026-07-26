from django.db import models
from django.contrib.auth.models import User

class UserPortfolio(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    stocks_units = models.FloatField(default=0.0)
    mf_units = models.FloatField(default=0.0)
    gold_units = models.FloatField(default=0.0)
    reits_units = models.FloatField(default=0.0)

class BrokerCredentials(models.Model):
    BROKER_CHOICES = [
        ('ANGELONE', 'Angel One'),
        ('ZERODHA', 'Zerodha Kite'),
        ('UPSTOX', 'Upstox'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='broker_creds')
    broker_name = models.CharField(max_length=50, choices=BROKER_CHOICES, default='ANGELONE')
    api_key = models.CharField(max_length=255, blank=True, null=True)
    client_id = models.CharField(max_length=100, blank=True, null=True)
    pin = models.CharField(max_length=50, blank=True, null=True)
    totp_secret = models.CharField(max_length=255, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_broker_name_display()}"