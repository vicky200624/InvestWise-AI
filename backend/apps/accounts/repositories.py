from django.contrib.auth import get_user_model
User = get_user_model()
from .models import UserPortfolio, BrokerCredentials

class AccountsRepository:
    @staticmethod
    def get_user_by_email(email: str):
        return User.objects.filter(email=email).first()
    
    @staticmethod
    def get_or_create_portfolio(user: User):
        return UserPortfolio.objects.get_or_create(user=user)
        
    @staticmethod
    def get_or_create_broker_credentials(user: User):
        return BrokerCredentials.objects.get_or_create(user=user)

    @staticmethod
    def save_broker_credentials(creds: BrokerCredentials):
        creds.save()
        return creds
