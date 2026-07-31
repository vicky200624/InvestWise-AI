from rest_framework import serializers
from .models import Watchlist, WatchlistItem, PriceAlert

class WatchlistItemSerializer(serializers.ModelSerializer):
    watchlist = serializers.PrimaryKeyRelatedField(
        queryset=Watchlist.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = WatchlistItem
        fields = ('id', 'watchlist', 'symbol', 'added_at')
        read_only_fields = ('id', 'added_at')
        validators = []

    def create(self, validated_data):
        watchlist = validated_data.get('watchlist')
        if not watchlist:
            user = self.context['request'].user
            watchlist, _ = Watchlist.objects.get_or_create(
                user=user,
                defaults={'name': 'Default Watchlist'}
            )
            validated_data['watchlist'] = watchlist
        symbol = validated_data.get('symbol')
        item, _ = WatchlistItem.objects.get_or_create(
            watchlist=watchlist,
            symbol=symbol,
            defaults=validated_data
        )
        return item



class WatchlistSerializer(serializers.ModelSerializer):
    items = WatchlistItemSerializer(many=True, read_only=True)

    class Meta:
        model = Watchlist
        fields = ('id', 'name', 'created_at', 'items')
        read_only_fields = ('id', 'created_at')

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)

class PriceAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceAlert
        fields = ('id', 'symbol', 'target_price', 'condition', 'is_active', 'created_at', 'triggered_at')
        read_only_fields = ('id', 'created_at', 'triggered_at')

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)
