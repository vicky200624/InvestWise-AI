from rest_framework import generics, views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User

from .serializers import UserRegistrationSerializer, UserSerializer, UserPortfolioSerializer, BrokerCredentialsSerializer
from .models import UserPortfolio, BrokerCredentials
from .services import AccountsService

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserRegistrationSerializer

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

