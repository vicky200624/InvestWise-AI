from rest_framework import serializers
from core.validators import ValidatedSymbolField
from .models import StockAnalysis, AgentTask, InvestmentFeedback, TrainedModel, MacroIndicator

class StockAnalysisSerializer(serializers.ModelSerializer):
    stock_symbol = ValidatedSymbolField()
    
    class Meta:
        model = StockAnalysis
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'investment_score', 'confidence', 'recommendation',
                            'fundamental_score', 'quant_score', 'sentiment_score', 'fundamental_data',
                            'quant_data', 'sentiment_data', 'shap_values', 'top_factors', 'nn_model_used',
                            'predicted_price', 'current_price', 'prediction_horizon_days',
                            'portfolio_suggestion', 'processing_time_seconds')

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)

class AgentTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentTask
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'completed_at', 'status', 'progress_percent',
                            'current_step', 'celery_task_id', 'result_data', 'error_message')

class InvestmentFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvestmentFeedback
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'reward_signal')

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)

class TrainedModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainedModel
        fields = '__all__'
        read_only_fields = ('id', 'created_at')

class MacroIndicatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = MacroIndicator
        fields = '__all__'
        read_only_fields = ('id',)
