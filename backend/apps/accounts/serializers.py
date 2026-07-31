from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserPortfolio, BrokerCredentials

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')
        read_only_fields = ('id',)

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'first_name', 'last_name')

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class UserPortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPortfolio
        fields = ('id', 'total_invested', 'current_value', 'xirr', 'last_synced')
        read_only_fields = ('id', 'total_invested', 'current_value', 'xirr', 'last_synced')

class BrokerCredentialsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrokerCredentials
        fields = ('id', 'broker_name', 'client_id', 'is_active', 'connected_at', 'api_key', 'pin', 'totp_secret')
        read_only_fields = ('id', 'is_active', 'connected_at')
        extra_kwargs = {
            'api_key': {'write_only': True},
            'pin': {'write_only': True},
            'totp_secret': {'write_only': True}
        }
