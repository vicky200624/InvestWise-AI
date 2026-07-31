from django.contrib.auth.models import User
from .models import UserPortfolio, BrokerCredentials

class AccountsService:
    @staticmethod
    def get_or_create_portfolio(user: User) -> UserPortfolio:
        portfolio, created = UserPortfolio.objects.get_or_create(user=user)
        return portfolio

    @staticmethod
    def update_broker_credentials(user: User, data: dict) -> BrokerCredentials:
        creds, created = BrokerCredentials.objects.get_or_create(user=user)
        if 'broker_name' in data:
            creds.broker_name = data['broker_name']
        if 'client_id' in data:
            creds.client_id = data['client_id']
        if 'api_key' in data:
            creds.api_key = data['api_key']
        if 'pin' in data:
            creds.pin = data['pin']
        if 'totp_secret' in data:
            creds.totp_secret = data['totp_secret']
        creds.is_active = True
        creds.save()
        return creds
