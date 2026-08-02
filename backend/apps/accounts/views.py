from rest_framework import generics, views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model

from .serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    UserPortfolioSerializer,
    BrokerCredentialsSerializer,
)
from .models import UserPortfolio, BrokerCredentials
from .services import AccountsService

# Fetch the active user model dynamically
User = get_user_model()


class ThrottledTokenObtainPairView(TokenObtainPairView):
    """
    JWT login endpoint with rate limiting to prevent brute-force attacks.
    """
    permission_classes = (AllowAny,)
    throttle_scope = 'auth'


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserRegistrationSerializer
    throttle_scope = 'auth'


class ProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class LogoutView(views.APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        # JWT logout is typically handled on client side by discarding tokens,
        # or by blacklisting the refresh token if configured.
        return Response(status=status.HTTP_204_NO_CONTENT)


class BrokerCredentialsView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = BrokerCredentialsSerializer

    def get_object(self):
        creds, _ = BrokerCredentials.objects.get_or_create(user=self.request.user)
        return creds


class UserPortfolioView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserPortfolioSerializer

    def get_object(self):
        portfolio, _ = UserPortfolio.objects.get_or_create(user=self.request.user)
        return portfolio


class RegisterOrLinkView(views.APIView):
    permission_classes = (AllowAny,)
    throttle_scope = 'auth'

    def post(self, request):
        email = request.data.get('email')

        # 1. Check for duplicates
        is_duplicate = AccountsService.check_duplicate_email(email)

        if is_duplicate:
            return Response(
                {"error": "An account with this email already exists. Please log in."},
                status=status.HTTP_409_CONFLICT
            )

        # 2. Proceed with creating a new account if no duplicate is found
        return Response({"message": "Account created!"}, status=status.HTTP_201_CREATED)
