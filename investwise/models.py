"""
InvestWise AI 3.0 — Database Models

Contains all Django ORM models for the platform:
- EXISTING (preserved): UserPortfolio, BrokerCredentials, AssetHolding, ChatSession, ChatMessage
- NEW: StockAnalysis, AgentTask, RAGDocument, InvestmentFeedback, TrainedModel, MacroIndicator

All new models support the 4-cluster agentic AI architecture, time-horizon
neural network routing, RAG memory, RLHF feedback loops, and ML model versioning.
"""
import uuid
from django.db import models
from django.contrib.auth.models import User


# ==============================================================================
# EXISTING MODELS (Preserved from InvestWise 2.x)
# ==============================================================================

class UserPortfolio(models.Model):
    """Legacy portfolio summary with unit counts per asset class."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    stocks_units = models.FloatField(default=0.0)
    mf_units = models.FloatField(default=0.0)
    gold_units = models.FloatField(default=0.0)
    reits_units = models.FloatField(default=0.0)

    def __str__(self):
        return f"Portfolio: {self.user.username}"


class BrokerCredentials(models.Model):
    """Stores encrypted broker API credentials for live trading integration."""
    BROKER_CHOICES = [
        ('ANGELONE', 'Angel One'),
        ('ZERODHA', 'Zerodha Kite'),
        ('UPSTOX', 'Upstox'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='broker_creds')
    broker_name = models.CharField(max_length=50, choices=BROKER_CHOICES, default='ANGELONE')
    api_key = models.CharField(max_length=255, blank=True, null=True)
    client_id = models.CharField(max_length=100, blank=True, null=True)
    pin = models.CharField(max_length=50, blank=True, null=True)
    totp_secret = models.CharField(max_length=255, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_broker_name_display()}"


class AssetHolding(models.Model):
    """Manual holdings for non-broker assets (Mutual Funds, Gold/SGB, REITs)."""
    ASSET_TYPES = [
        ('MF', 'Mutual Fund'),
        ('GOLD', 'Gold & SGB'),
        ('REIT', 'REIT'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='manual_holdings')
    asset_type = models.CharField(max_length=10, choices=ASSET_TYPES)
    symbol = models.CharField(max_length=50, help_text="Yahoo Finance Ticker (e.g. MON100.NS)")
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, help_text="Short Display Code (e.g. PP, SGB)")
    qty = models.FloatField(default=0.0)
    avg_price = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.user.username} - {self.name} ({self.get_asset_type_display()})"


class ChatSession(models.Model):
    """Groups chat messages into named conversation sessions."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, default="New Conversation")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.user.username})"


class ChatMessage(models.Model):
    """Individual chat message within a session (user or AI role)."""
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10)  # 'user' or 'ai'
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.role}: {self.content[:30]}"


# ==============================================================================
# NEW MODELS — InvestWise AI 3.0 Agentic Architecture
# ==============================================================================

class StockAnalysis(models.Model):
    """
    Stores the complete output of an AI analysis run for a stock.

    Each record represents one full pass through the 4-cluster LangGraph pipeline:
    Fundamental → Quant/Valuation → Market Intelligence → Portfolio/Guardrails.

    The investment_score (0-100) is the fused XGBoost output from the Decision Cluster.
    SHAP values are stored as JSON for the frontend explainability waterfall chart.
    """
    TIME_HORIZON_CHOICES = [
        ('SHORT', 'Short-Term (1-30 days)'),
        ('LONG', 'Long-Term (3-12+ months)'),
    ]
    RECOMMENDATION_CHOICES = [
        ('STRONG_BUY', 'Strong Buy'),
        ('BUY', 'Buy'),
        ('HOLD', 'Hold'),
        ('SELL', 'Sell'),
        ('STRONG_SELL', 'Strong Sell'),
    ]
    NN_MODEL_CHOICES = [
        ('LSTM', 'LSTM (Long Short-Term Memory)'),
        ('GRU', 'GRU (Gated Recurrent Unit)'),
        ('FNN', 'FNN (Feedforward Neural Network)'),
        ('ENSEMBLE', 'Ensemble (Multiple Models)'),
    ]

    # --- Core Fields ---
    stock_symbol = models.CharField(max_length=20, db_index=True)
    stock_name = models.CharField(max_length=200, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analyses')
    time_horizon = models.CharField(max_length=10, choices=TIME_HORIZON_CHOICES)

    # --- Fused Investment Score ---
    investment_score = models.FloatField(
        help_text="Final 0-100 score from XGBoost Decision Cluster"
    )
    confidence = models.FloatField(
        help_text="Model confidence as a probability (0.0-1.0)"
    )
    recommendation = models.CharField(max_length=20, choices=RECOMMENDATION_CHOICES)

    # --- Individual Cluster Scores (0-100 each) ---
    fundamental_score = models.FloatField(null=True, blank=True)
    quant_score = models.FloatField(null=True, blank=True)
    sentiment_score = models.FloatField(null=True, blank=True)

    # --- Cluster Detail Data (full outputs from each sub-graph) ---
    fundamental_data = models.JSONField(
        null=True, blank=True,
        help_text="Full output from Fundamental Analysis Cluster"
    )
    quant_data = models.JSONField(
        null=True, blank=True,
        help_text="Full output from Quant & Valuation Cluster (DCF, technicals)"
    )
    sentiment_data = models.JSONField(
        null=True, blank=True,
        help_text="Full output from Market Intelligence Cluster (news, macro)"
    )

    # --- SHAP Explainability ---
    shap_values = models.JSONField(
        null=True, blank=True,
        help_text="SHAP values array for the XGBoost prediction"
    )
    top_factors = models.JSONField(
        null=True, blank=True,
        help_text="Top 10 driving factors: [{name, value, impact}, ...]"
    )

    # --- Neural Network Prediction ---
    nn_model_used = models.CharField(
        max_length=10, choices=NN_MODEL_CHOICES,
        help_text="Which NN architecture was routed based on time horizon"
    )
    predicted_price = models.FloatField(
        null=True, blank=True,
        help_text="Neural network's price prediction for the target horizon"
    )
    current_price = models.FloatField(
        null=True, blank=True,
        help_text="Current market price at time of analysis"
    )
    prediction_horizon_days = models.IntegerField(
        help_text="Number of days into the future the prediction targets"
    )

    # --- Portfolio Optimization Suggestion ---
    portfolio_suggestion = models.JSONField(
        null=True, blank=True,
        help_text="Markowitz/Black-Litterman optimal allocation suggestion"
    )

    # --- Metadata ---
    created_at = models.DateTimeField(auto_now_add=True)
    processing_time_seconds = models.FloatField(
        null=True, blank=True,
        help_text="Total wall-clock time for the full analysis pipeline"
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['stock_symbol', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return (
            f"{self.stock_symbol} | Score: {self.investment_score:.0f} | "
            f"{self.recommendation} | {self.time_horizon}"
        )


class AgentTask(models.Model):
    """
    Tracks the lifecycle of async LangGraph agent execution tasks.

    When a user requests a stock analysis, a Celery task is dispatched and
    an AgentTask record is created to track its progress. The frontend polls
    this via REST API or receives real-time updates via WebSocket.

    Status flow: PENDING → RUNNING → COMPLETED / FAILED
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RUNNING', 'Running'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]
    TASK_TYPE_CHOICES = [
        ('full_analysis', 'Full Stock Analysis'),
        ('fundamental_only', 'Fundamental Analysis Only'),
        ('sentiment_only', 'Sentiment Analysis Only'),
        ('portfolio_optimize', 'Portfolio Optimization'),
        ('retrain_model', 'Model Retraining'),
        ('ingest_filing', 'SEC Filing Ingestion'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='agent_tasks')
    task_type = models.CharField(max_length=50, choices=TASK_TYPE_CHOICES)
    celery_task_id = models.CharField(
        max_length=255, null=True, blank=True,
        help_text="Celery async result ID for task management"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    # --- Input/Output ---
    input_data = models.JSONField(
        help_text="Task input parameters: {symbol, time_horizon, ...}"
    )
    result_data = models.JSONField(
        null=True, blank=True,
        help_text="Task output (analysis_id, scores, etc.)"
    )
    error_message = models.TextField(null=True, blank=True)

    # --- Progress Tracking ---
    current_step = models.CharField(
        max_length=100, blank=True, default='',
        help_text="Current processing step for real-time UI updates"
    )
    progress_percent = models.IntegerField(
        default=0,
        help_text="Completion percentage (0-100) for progress bar"
    )

    # --- Timestamps ---
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['celery_task_id']),
        ]

    def __str__(self):
        return f"[{self.status}] {self.task_type} for {self.user.username}"


class RAGDocument(models.Model):
    """
    Metadata registry for documents ingested into the ChromaDB vector store.

    Each RAGDocument represents a source document (SEC filing, earnings transcript,
    news article) that has been chunked, embedded, and stored in ChromaDB.
    The chroma_collection field links to the ChromaDB collection name.
    """
    SOURCE_TYPE_CHOICES = [
        ('SEC_10K', 'SEC 10-K Annual Report'),
        ('SEC_10Q', 'SEC 10-Q Quarterly Report'),
        ('SEC_8K', 'SEC 8-K Current Report'),
        ('EARNINGS', 'Earnings Call Transcript'),
        ('NEWS', 'News Article'),
        ('RESEARCH', 'Research Report'),
    ]

    source_type = models.CharField(max_length=20, choices=SOURCE_TYPE_CHOICES)
    stock_symbol = models.CharField(max_length=20, db_index=True)
    title = models.CharField(max_length=500)
    source_url = models.URLField(null=True, blank=True)
    filing_date = models.DateField(
        null=True, blank=True,
        help_text="Date of the original filing/publication"
    )

    # --- ChromaDB Reference ---
    chroma_collection = models.CharField(
        max_length=100,
        help_text="ChromaDB collection name where chunks are stored"
    )
    chunk_count = models.IntegerField(
        default=0,
        help_text="Number of text chunks created from this document"
    )

    # --- Metadata ---
    ingested_at = models.DateTimeField(auto_now_add=True)
    file_size_bytes = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['-ingested_at']
        indexes = [
            models.Index(fields=['stock_symbol', 'source_type']),
        ]

    def __str__(self):
        return f"[{self.source_type}] {self.stock_symbol}: {self.title[:60]}"


class InvestmentFeedback(models.Model):
    """
    User feedback on AI-generated investment recommendations.

    This data feeds into the RLHF (Reinforcement Learning from Human Feedback)
    reward model to dynamically adjust feature weights in the Decision Cluster.

    The actual_outcome field is populated retroactively (e.g., via a periodic
    Celery task) to measure how well the AI's recommendation performed.
    """
    FEEDBACK_CHOICES = [
        ('BUY_AGREE', 'Agreed with Buy'),
        ('HOLD_AGREE', 'Agreed with Hold'),
        ('SELL_AGREE', 'Agreed with Sell'),
        ('REJECT', 'Rejected Recommendation'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='investment_feedbacks')
    analysis = models.ForeignKey(
        StockAnalysis, on_delete=models.CASCADE, related_name='feedbacks'
    )
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_CHOICES)
    comment = models.TextField(
        blank=True,
        help_text="Optional user comment explaining their feedback"
    )

    # --- Outcome Tracking (filled retroactively) ---
    actual_outcome = models.FloatField(
        null=True, blank=True,
        help_text="Actual return % measured after the prediction horizon"
    )
    outcome_measured_at = models.DateTimeField(null=True, blank=True)

    # --- RLHF Reward Signal ---
    reward_signal = models.FloatField(
        null=True, blank=True,
        help_text="Computed reward value for the RLHF model: "
                  "+1.0 (correct agree), -1.0 (incorrect agree), "
                  "+0.5 (correct reject), -0.5 (incorrect reject)"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['analysis', 'feedback_type']),
        ]

    def __str__(self):
        return (
            f"{self.user.username} → {self.analysis.stock_symbol}: "
            f"{self.feedback_type}"
        )


class TrainedModel(models.Model):
    """
    Registry of trained ML model artifacts with versioning and performance tracking.

    Stores metadata for LSTM, GRU, FNN, XGBoost, and CatBoost models.
    The file_path points to the serialized model file in the AI_MODEL_DIR.
    Only one model per (model_type, stock_symbol) should have is_active=True.
    """
    MODEL_TYPE_CHOICES = [
        ('LSTM', 'LSTM (Long Short-Term Memory)'),
        ('GRU', 'GRU (Gated Recurrent Unit)'),
        ('FNN', 'FNN (Feedforward Neural Network)'),
        ('XGBOOST', 'XGBoost Gradient Boosting'),
        ('CATBOOST', 'CatBoost Gradient Boosting'),
        ('REWARD', 'RLHF Reward Model'),
    ]

    model_type = models.CharField(max_length=20, choices=MODEL_TYPE_CHOICES)
    stock_symbol = models.CharField(
        max_length=20, null=True, blank=True,
        help_text="Null = general-purpose model (not stock-specific)"
    )
    version = models.IntegerField(default=1)
    file_path = models.CharField(
        max_length=500,
        help_text="Absolute path to the serialized model file"
    )

    # --- Performance Metrics ---
    metrics = models.JSONField(
        help_text="Training/validation metrics: {rmse, mae, r2, accuracy, ...}"
    )
    training_samples = models.IntegerField(
        null=True, blank=True,
        help_text="Number of training samples used"
    )
    feature_count = models.IntegerField(
        null=True, blank=True,
        help_text="Number of input features"
    )

    # --- Lifecycle ---
    is_active = models.BooleanField(
        default=True,
        help_text="Only one active model per (model_type, stock_symbol)"
    )
    trained_at = models.DateTimeField(auto_now_add=True)
    training_duration_seconds = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['-trained_at']
        indexes = [
            models.Index(fields=['model_type', 'stock_symbol', 'is_active']),
        ]

    def __str__(self):
        symbol = self.stock_symbol or 'GENERAL'
        return f"{self.model_type} v{self.version} [{symbol}] {'✓' if self.is_active else '✗'}"


class MacroIndicator(models.Model):
    """
    Cached macroeconomic data from FRED API and World Bank.

    Stores time-series macro data (GDP, inflation, interest rates, etc.)
    locally to avoid redundant API calls. Refreshed periodically via
    a Celery Beat scheduled task.
    """
    SOURCE_CHOICES = [
        ('FRED', 'Federal Reserve Economic Data'),
        ('WORLDBANK', 'World Bank Open Data'),
    ]

    indicator_code = models.CharField(
        max_length=50, db_index=True,
        help_text="FRED series ID (e.g., GDP, CPIAUCSL, FEDFUNDS, DGS10)"
    )
    indicator_name = models.CharField(
        max_length=200, blank=True,
        help_text="Human-readable indicator name"
    )
    date = models.DateField()
    value = models.FloatField()
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='FRED')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['indicator_code', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['indicator_code', '-date']),
        ]

    def __str__(self):
        return f"{self.indicator_code} | {self.date} | {self.value}"