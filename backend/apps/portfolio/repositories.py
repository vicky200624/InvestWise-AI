from django.contrib.auth import get_user_model
User = get_user_model()
from .models import AssetHolding
from apps.accounts.models import UserPortfolio, BrokerCredentials

class PortfolioRepository:
    @staticmethod
    def get_asset_holdings_by_user(user: User):
        # Optimize query with select_related to avoid N+1
        return AssetHolding.objects.filter(user=user).select_related('user')

    @staticmethod
    def get_or_create_portfolio(user: User):
        portfolio, created = UserPortfolio.objects.get_or_create(user=user)
        return portfolio

    @staticmethod
    def get_broker_credentials_active(user: User):
        try:
            # Use get_object_or_None pattern for better performance
            return BrokerCredentials.objects.select_related('user').get(user=user, is_active=True)
        except BrokerCredentials.DoesNotExist:
            return None

    @staticmethod
    def update_or_create_asset_holding(user: User, symbol: str, defaults: dict):
        return AssetHolding.objects.update_or_create(
            user=user,
            symbol=symbol,
            defaults=defaults
        )
