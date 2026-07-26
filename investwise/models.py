import uuid
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

class AssetHolding(models.Model):
    ASSET_TYPES = [
        ('MF', 'Mutual Fund'),
        ('GOLD', 'Gold & SGB'),
        ('REIT', 'REIT'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='manual_holdings')
    asset_type = models.CharField(max_length=10, choices=ASSET_TYPES)
    symbol = models.CharField(max_length=50, help_text="Yahoo Finance Ticker (e.g. MON100.NS)") 
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, help_text="Short Display Code (e.g. PP, SGB)")
    qty = models.FloatField(default=0.0)
    avg_price = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.user.username} - {self.name} ({self.get_asset_type_display()})"


class ChatSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, default="New Conversation")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.user.username})"

class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10) # 'user' or 'ai'
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.role}: {self.content[:30]}"