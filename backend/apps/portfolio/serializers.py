from rest_framework import serializers
from .models import AssetHolding

class AssetHoldingSerializer(serializers.ModelSerializer):
    shares = serializers.FloatField(source='qty', read_only=True)
    
    # Expose both camelCase and snake_case variants for every computed metric
    currentPrice = serializers.SerializerMethodField()
    current_price = serializers.SerializerMethodField()
    
    totalValue = serializers.SerializerMethodField()
    total_value = serializers.SerializerMethodField()
    
    returnValue = serializers.SerializerMethodField()
    return_value = serializers.SerializerMethodField()
    
    returnPercent = serializers.SerializerMethodField()
    return_percent = serializers.SerializerMethodField()
    
    # Explicit percentage fields for UI table cells
    profit_loss_percent = serializers.SerializerMethodField()
    pnl_percentage = serializers.SerializerMethodField()

    class Meta:
        model = AssetHolding
        fields = [
            'id', 'asset_type', 'symbol', 'name', 'code', 'qty', 'shares', 'avg_price',
            'currentPrice', 'current_price',
            'totalValue', 'total_value',
            'returnValue', 'return_value',
            'returnPercent', 'return_percent',
            'profit_loss_percent', 'pnl_percentage',
            'added_at'
        ]

    def _get_cp(self, obj):
        cp = getattr(obj, 'current_price', 0.0)
        return float(cp) if cp and cp > 0 else float(obj.avg_price or 0.0)

    def get_currentPrice(self, obj): return self._get_cp(obj)
    def get_current_price(self, obj): return self._get_cp(obj)

    def get_totalValue(self, obj): return round((obj.qty or 0.0) * self._get_cp(obj), 2)
    def get_total_value(self, obj): return self.get_totalValue(obj)

    def get_returnValue(self, obj):
        cp = self._get_cp(obj)
        return round((cp - (obj.avg_price or 0.0)) * (obj.qty or 0.0), 2)
    def get_return_value(self, obj): return self.get_returnValue(obj)

    def get_returnPercent(self, obj):
        avg = float(obj.avg_price or 0.0)
        if avg > 0:
            cp = self._get_cp(obj)
            return round(((cp - avg) / avg) * 100.0, 2)
        return 0.0
    
    def get_return_percent(self, obj): return self.get_returnPercent(obj)
    def get_profit_loss_percent(self, obj): return self.get_returnPercent(obj)
    def get_pnl_percentage(self, obj): return self.get_returnPercent(obj)