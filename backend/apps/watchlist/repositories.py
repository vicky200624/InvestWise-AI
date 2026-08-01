from django.contrib.auth import get_user_model
User = get_user_model()
from .models import Watchlist, WatchlistItem, PriceAlert

class WatchlistRepository:
    @staticmethod
    def get_watchlists_by_user(user: User):
        return Watchlist.objects.filter(user=user)

    @staticmethod
    def get_watchlist_items_by_user(user: User):
        return WatchlistItem.objects.filter(watchlist__user=user)

    @staticmethod
    def get_price_alerts_by_user(user: User):
        return PriceAlert.objects.filter(user=user)
