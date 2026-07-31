from rest_framework import generics, views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model

# Fetch the active user model dynamically
User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    # ... the rest of your view stays exactly the same


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

from rest_framework import status, views
from rest_framework.response import Response
from django.contrib.auth import get_user_model

User = get_user_model()

class RegisterOrLinkView(views.APIView):
    def post(self, request):
        email = request.data.get('email')
        
        # 1. Check for duplicates
        user = User.objects.filter(email=email).first()
        
        if user:
            # If you are doing account linking (e.g., attaching a broker):
            # link_broker_to_account(user, request.data.get('broker_data'))
            # return Response({"message": "Account linked successfully."})
            
            # If this is just standard signup, reject the duplicate:
            return Response(
                {"error": "An account with this email already exists. Please log in."},
                status=status.HTTP_409_CONFLICT
            )
            
        # 2. Proceed with creating a new account if no duplicate is found
        # ... your creation logic here ...
        return Response({"message": "Account created!"}, status=status.HTTP_201_CREATED)
