from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Watchlist, WatchlistItem, PriceAlert
from .serializers import WatchlistSerializer, WatchlistItemSerializer, PriceAlertSerializer
from core.permissions import IsOwner

class WatchlistViewSet(viewsets.ModelViewSet):
    serializer_class = WatchlistSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        from .repositories import WatchlistRepository
        return WatchlistRepository.get_watchlists_by_user(self.request.user)

class WatchlistItemViewSet(viewsets.ModelViewSet):
    serializer_class = WatchlistItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        from .repositories import WatchlistRepository
        return WatchlistRepository.get_watchlist_items_by_user(self.request.user)



class PriceAlertViewSet(viewsets.ModelViewSet):
    serializer_class = PriceAlertSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        from .repositories import WatchlistRepository
        return WatchlistRepository.get_price_alerts_by_user(self.request.user)
