from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Watchlist, WatchlistItem, PriceAlert
from .serializers import WatchlistSerializer, WatchlistItemSerializer, PriceAlertSerializer
from core.permissions import IsOwner

class WatchlistViewSet(viewsets.ModelViewSet):
    serializer_class = WatchlistSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Watchlist.objects.filter(user=self.request.user)

class WatchlistItemViewSet(viewsets.ModelViewSet):
    serializer_class = WatchlistItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WatchlistItem.objects.filter(watchlist__user=self.request.user)



class PriceAlertViewSet(viewsets.ModelViewSet):
    serializer_class = PriceAlertSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        return PriceAlert.objects.filter(user=self.request.user)
