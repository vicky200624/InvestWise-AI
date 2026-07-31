from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WatchlistViewSet, WatchlistItemViewSet, PriceAlertViewSet

router = DefaultRouter()
router.register(r'watchlists', WatchlistViewSet, basename='watchlist')
router.register(r'items', WatchlistItemViewSet, basename='watchlist-item')
router.register(r'alerts', PriceAlertViewSet, basename='pricealert')

urlpatterns = [
    path('', include(router.urls)),
]
