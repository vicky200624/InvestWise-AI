"""
InvestWise AI 3.0 — Django Admin Configuration

Registers all models with the Django admin interface for
data management, debugging, and operational monitoring.
"""
from django.contrib import admin
from .models import (
    UserPortfolio,
    BrokerCredentials,
    AssetHolding,
    ChatSession,
    ChatMessage,
    StockAnalysis,
    AgentTask,
    RAGDocument,
    InvestmentFeedback,
    TrainedModel,
    MacroIndicator,
)


# ==============================================================================
# Existing Models (Preserved)
# ==============================================================================

admin.site.register(UserPortfolio)
admin.site.register(BrokerCredentials)
admin.site.register(AssetHolding)


# ==============================================================================
# New AI 3.0 Models — Enhanced Admin Views
# ==============================================================================

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at')
    list_filter = ('user', 'created_at')
    search_fields = ('title', 'user__username')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('role', 'user', 'content_preview', 'timestamp')
    list_filter = ('role', 'user')

    def content_preview(self, obj):
        return obj.content[:80]
    content_preview.short_description = 'Content'


@admin.register(StockAnalysis)
class StockAnalysisAdmin(admin.ModelAdmin):
    list_display = (
        'stock_symbol', 'investment_score', 'recommendation',
        'time_horizon', 'confidence', 'user', 'created_at'
    )
    list_filter = ('recommendation', 'time_horizon', 'nn_model_used')
    search_fields = ('stock_symbol', 'stock_name', 'user__username')
    readonly_fields = (
        'shap_values', 'top_factors', 'fundamental_data',
        'quant_data', 'sentiment_data', 'portfolio_suggestion'
    )


@admin.register(AgentTask)
class AgentTaskAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'task_type', 'status', 'progress_percent',
        'current_step', 'user', 'created_at'
    )
    list_filter = ('status', 'task_type')
    search_fields = ('id', 'user__username', 'celery_task_id')
    readonly_fields = ('input_data', 'result_data')


@admin.register(RAGDocument)
class RAGDocumentAdmin(admin.ModelAdmin):
    list_display = (
        'stock_symbol', 'source_type', 'title_preview',
        'chunk_count', 'ingested_at'
    )
    list_filter = ('source_type', 'stock_symbol')
    search_fields = ('title', 'stock_symbol')

    def title_preview(self, obj):
        return obj.title[:60]
    title_preview.short_description = 'Title'


@admin.register(InvestmentFeedback)
class InvestmentFeedbackAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'feedback_type', 'reward_signal',
        'actual_outcome', 'created_at'
    )
    list_filter = ('feedback_type',)
    search_fields = ('user__username', 'analysis__stock_symbol')


@admin.register(TrainedModel)
class TrainedModelAdmin(admin.ModelAdmin):
    list_display = (
        'model_type', 'stock_symbol', 'version',
        'is_active', 'trained_at'
    )
    list_filter = ('model_type', 'is_active')
    search_fields = ('stock_symbol',)


@admin.register(MacroIndicator)
class MacroIndicatorAdmin(admin.ModelAdmin):
    list_display = ('indicator_code', 'indicator_name', 'date', 'value', 'source')
    list_filter = ('indicator_code', 'source')
    search_fields = ('indicator_code', 'indicator_name')