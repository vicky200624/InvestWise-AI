from django.db import models
from django.contrib.auth.models import User

class AssetHolding(models.Model):
    ASSET_TYPES = [
        ('STOCK', 'Stock'), 
        ('MF', 'Mutual Fund'), 
        ('GOLD', 'Gold'), 
        ('REIT', 'REIT'), 
        ('BOND', 'Bond')
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='asset_holdings')
    asset_type = models.CharField(max_length=10, choices=ASSET_TYPES)
    symbol = models.CharField(max_length=20)
    name = models.CharField(max_length=200, blank=True)
    code = models.CharField(max_length=10, blank=True)
    qty = models.FloatField(default=0)
    avg_price = models.FloatField(default=0)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-added_at']

