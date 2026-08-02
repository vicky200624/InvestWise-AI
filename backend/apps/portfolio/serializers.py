from rest_framework import serializers
from core.validators import ValidatedSymbolField, ValidatedAmountField
from .models import AssetHolding

class AssetHoldingSerializer(serializers.ModelSerializer):
    symbol = ValidatedSymbolField()
    qty = ValidatedAmountField(min_value=0.0, max_value=1e9)
    avg_price = ValidatedAmountField(min_value=0.0, max_value=1e6)

    class Meta:
        model = AssetHolding
        fields = ('id', 'asset_type', 'symbol', 'name', 'code', 'qty', 'avg_price', 'added_at')
        read_only_fields = ('id', 'added_at')

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)
