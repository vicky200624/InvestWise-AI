from django.contrib.auth import get_user_model
User = get_user_model()
from django.conf import settings
from .models import UserPortfolio, BrokerCredentials
from .repositories import AccountsRepository

class AccountsService:
    @staticmethod
    def get_or_create_portfolio(user: User) -> UserPortfolio:
        portfolio, created = AccountsRepository.get_or_create_portfolio(user)
        return portfolio

    @staticmethod
    def update_broker_credentials(user: User, data: dict) -> BrokerCredentials:
        creds, created = AccountsRepository.get_or_create_broker_credentials(user)
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
        return AccountsRepository.save_broker_credentials(creds)

    @staticmethod
    def check_duplicate_email(email: str) -> bool:
        user = AccountsRepository.get_user_by_email(email)
        return user is not None
