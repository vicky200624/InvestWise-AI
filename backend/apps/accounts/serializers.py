from django.contrib.auth import get_user_model
User = get_user_model()
from rest_framework import serializers
from django.conf import settings
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
    broker_name = serializers.CharField(max_length=20, default='ANGELONE')
    api_key = serializers.CharField(write_only=True, required=False, allow_blank=True)
    pin = serializers.CharField(write_only=True, required=False, allow_blank=True)
    totp_secret = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = BrokerCredentials
        fields = ('id', 'broker_name', 'client_id', 'is_active', 'connected_at', 'api_key', 'pin', 'totp_secret')
        read_only_fields = ('id', 'is_active', 'connected_at')

    def validate_broker_name(self, value):
        val = value.upper() if value else 'ANGELONE'
        valid_choices = [c[0] for c in BrokerCredentials.BROKER_CHOICES]
        if val not in valid_choices:
            raise serializers.ValidationError(f"Invalid broker name. Valid choices: {valid_choices}")
        return val



