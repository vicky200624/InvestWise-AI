import yfinance as yf
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Watchlist, WatchlistItem, PriceAlert
from .serializers import WatchlistSerializer, WatchlistItemSerializer, PriceAlertSerializer
from core.permissions import IsOwner


class WatchlistViewSet(viewsets.ModelViewSet):
    serializer_class = WatchlistSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    pagination_class = None # Disables pagination to output a flat array

    def get_queryset(self):
        from .repositories import WatchlistRepository
        return WatchlistRepository.get_watchlists_by_user(self.request.user)


class WatchlistItemViewSet(viewsets.ModelViewSet):
    serializer_class = WatchlistItemSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None # Disables pagination to fix the React map error

    def get_queryset(self):
        from .repositories import WatchlistRepository
        return WatchlistRepository.get_watchlist_items_by_user(self.request.user)

    def list(self, request, *args, **kwargs):
        """Intercept list response to fetch real live prices and day change via yfinance."""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data

        for item in data:
            symbol = item.get('symbol', '')
            if not symbol:
                continue

            try:
                # 1. Fetch live global ticker data (e.g. NVDA, AMZN)
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1d")

                # 2. Fallback to NSE format if symbol is an Indian stock (e.g. RELIANCE)
                if hist.empty:
                    ticker = yf.Ticker(f"{symbol}.NS")
                    hist = ticker.history(period="1d")

                if not hist.empty:
                    close_val = float(hist['Close'].iloc[-1])
                    open_val = float(hist['Open'].iloc[-1]) if float(hist['Open'].iloc[-1]) > 0 else close_val
                    day_change = ((close_val - open_val) / open_val) * 100.0

                    # Map dynamic data for frontend consumption
                    item['currentPrice'] = round(close_val, 2)
                    item['current_price'] = round(close_val, 2)
                    item['dayChange'] = round(day_change, 2)
                    item['day_change'] = round(day_change, 2)
                else:
                    item['currentPrice'] = item.get('target_price', 0.0)
                    item['dayChange'] = 0.0
            except Exception:
                item['currentPrice'] = item.get('target_price', 0.0)
                item['dayChange'] = 0.0

        return Response(data)


class PriceAlertViewSet(viewsets.ModelViewSet):
    serializer_class = PriceAlertSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    pagination_class = None # Disables pagination

    def get_queryset(self):
        from .repositories import WatchlistRepository
        return WatchlistRepository.get_price_alerts_by_user(self.request.user)