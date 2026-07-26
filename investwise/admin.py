from django.contrib import admin
from .models import UserPortfolio, BrokerCredentials, AssetHolding

admin.site.register(UserPortfolio)
admin.site.register(BrokerCredentials)
admin.site.register(AssetHolding)