from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    RegisterView, ProfileView, LogoutView,
    BrokerCredentialsView, UserPortfolioView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('refresh/', TokenRefreshView.as_view(), name='refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('broker/', BrokerCredentialsView.as_view(), name='broker-credentials'),
    path('portfolio/', UserPortfolioView.as_view(), name='user-portfolio'),
]
