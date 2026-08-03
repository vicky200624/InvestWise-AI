from django.contrib.auth import get_user_model
from .models import AssetHolding
from apps.accounts.models import UserPortfolio, BrokerCredentials

User = get_user_model()


class PortfolioRepository:
    @staticmethod
    def get_asset_holdings_by_user(user: User):
        return AssetHolding.objects.filter(user=user)

    @staticmethod
    def get_or_create_portfolio(user: User):
        portfolio, _ = UserPortfolio.objects.get_or_create(user=user)
        return portfolio

    @staticmethod
    def get_broker_credentials_active(user: User):
        try:
            return BrokerCredentials.objects.select_related('user').get(user=user, is_active=True)
        except BrokerCredentials.DoesNotExist:
            return None

    @staticmethod
    def update_or_create_asset_holding(user: User, symbol: str, defaults: dict):
        holding, created = AssetHolding.objects.update_or_create(
            user=user,
            symbol=symbol,
            defaults=defaults
        )

        portfolio, _ = UserPortfolio.objects.get_or_create(user=user)
        all_holdings = AssetHolding.objects.filter(user=user)
        
        total_invested = sum(h.qty * h.avg_price for h in all_holdings)
        total_current = sum(h.qty * (getattr(h, 'current_price', 0) or h.avg_price) for h in all_holdings)

        portfolio.total_invested = total_invested
        portfolio.current_value = total_current
        portfolio.save(update_fields=['total_invested', 'current_value'])

        return holding