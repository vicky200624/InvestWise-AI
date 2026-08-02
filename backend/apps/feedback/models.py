from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from apps.research.models import StockAnalysis


class Feedback(models.Model):
    """
    Comprehensive feedback database capturing every user interaction.
    """
    FEEDBACK_TYPES = [
        ('BUY_ACCEPTED', 'BUY Accepted'),
        ('BUY_REJECTED', 'BUY Rejected'),
        ('SELL_ACCEPTED', 'SELL Accepted'),
        ('SELL_REJECTED', 'SELL Rejected'),
        ('HOLD_ACCEPTED', 'HOLD Accepted'),
        ('HOLD_REJECTED', 'HOLD Rejected'),
        ('PORTFOLIO_MODIFIED', 'Portfolio Modified'),
        ('WATCHLIST_ADDED', 'Watchlist Added'),
        ('WATCHLIST_REMOVED', 'Watchlist Removed'),
        ('COMPANY_FOLLOWED', 'Company Followed'),
        ('RESEARCH_READ', 'Research Read'),
        ('MANUAL_RATING', 'Manual Rating'),
        ('RISK_PREF_CHANGED', 'Risk Preference Changed'),
        ('HORIZON_CHANGED', 'Investment Horizon Changed'),
    ]

    ACTION_TYPES = [
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('IGNORED', 'Ignored'),
        ('MODIFIED', 'Modified'),
        ('FOLLOWED', 'Followed'),
        ('READ', 'Read'),
        ('RATED', 'Rated'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='feedbacks')
    analysis = models.ForeignKey(StockAnalysis, on_delete=models.CASCADE, related_name='feedbacks', null=True, blank=True)
    recommendation_id = models.CharField(max_length=100, db_index=True)
    company = models.CharField(max_length=100, db_index=True)
    symbol = models.CharField(max_length=20, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    feedback_type = models.CharField(max_length=30, choices=FEEDBACK_TYPES)
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    reason = models.TextField(blank=True)
    
    # Portfolio state
    portfolio_before = models.JSONField(default=dict, blank=True)
    portfolio_after = models.JSONField(default=dict, blank=True)
    
    # User context at time of feedback
    risk_profile = models.CharField(max_length=20, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    model_version = models.CharField(max_length=50, blank=True)
    
    # Reward calculation
    reward_signal = models.FloatField(null=True, blank=True)
    sample_weight = models.FloatField(null=True, blank=True)
    
    # Outcome tracking
    actual_return_percent = models.FloatField(null=True, blank=True)
    outcome_evaluated = models.BooleanField(default=False)
    outcome_evaluated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'symbol', 'timestamp']),
            models.Index(fields=['feedback_type', 'timestamp']),
            models.Index(fields=['model_version', 'timestamp']),
        ]


class UserPreferenceProfile(models.Model):
    """
    Adaptive learning: User profile memory storing learned preferences.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='preference_profile')
    
    # Risk and investment preferences
    risk_tolerance = models.CharField(max_length=20, default='MODERATE')
    investment_goals = models.JSONField(default=list, blank=True)
    target_cagr = models.FloatField(null=True, blank=True)
    
    # Learned preferences (updated by learning engine)
    preferred_sectors = models.JSONField(default=list, blank=True)
    preferred_companies = models.JSONField(default=list, blank=True)
    preferred_risk_level = models.FloatField(default=0.5)
    preferred_investment_horizon = models.CharField(max_length=20, blank=True)
    preferred_dividend_strategy = models.BooleanField(default=False)
    preferred_growth_strategy = models.BooleanField(default=True)
    preferred_value_strategy = models.BooleanField(default=False)
    
    # Behavioral patterns
    avg_holding_duration_days = models.IntegerField(null=True, blank=True)
    acceptance_rate = models.FloatField(default=0.0)
    total_feedback_count = models.IntegerField(default=0)
    
    # RLHF adjustments
    rlhf_ranking_boost = models.JSONField(default=dict, blank=True)
    rlhf_confidence_adjustment = models.FloatField(default=1.0)
    rlhf_priority_weights = models.JSONField(default=dict, blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'updated_at']),
        ]


class ConversationMemory(models.Model):
    """
    Conversation memory for context-aware interactions.
    Never expose private memory to other users.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conversation_memories')
    session_id = models.CharField(max_length=100, db_index=True)
    
    # Memory categories
    memory_type = models.CharField(max_length=30, choices=[
        ('RECENT_CONVERSATION', 'Recent Conversation'),
        ('RESEARCH_TOPIC', 'Research Topic'),
        ('PORTFOLIO_DISCUSSION', 'Portfolio Discussion'),
        ('COMPARISON', 'Company Comparison'),
        ('PREFERENCE', 'User Preference'),
    ])
    
    # Memory content
    entities = models.JSONField(default=list, blank=True)  # Companies, sectors, etc.
    summary = models.TextField(blank=True)
    key_points = models.JSONField(default=list, blank=True)
    sentiment = models.CharField(max_length=20, blank=True)
    
    # Context
    context_data = models.JSONField(default=dict, blank=True)
    relevance_score = models.FloatField(default=1.0)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    last_accessed = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_accessed']
        indexes = [
            models.Index(fields=['user', 'session_id', 'memory_type']),
        ]


class PortfolioMemory(models.Model):
    """
    Portfolio memory tracking historical and current state.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='portfolio_memories')
    
    # Holdings snapshot
    symbol = models.CharField(max_length=20, db_index=True)
    company_name = models.CharField(max_length=200, blank=True)
    qty = models.FloatField()
    avg_buy_price = models.FloatField()
    current_price = models.FloatField(null=True, blank=True)
    
    # Performance tracking
    holding_duration_days = models.IntegerField(default=0)
    realized_profit = models.FloatField(default=0.0)
    unrealized_profit = models.FloatField(default=0.0)
    risk_exposure = models.FloatField(default=0.0)
    
    # Allocation
    sector = models.CharField(max_length=100, blank=True)
    allocation_percent = models.FloatField(default=0.0)
    
    # Snapshot metadata
    snapshot_date = models.DateTimeField(auto_now_add=True)
    is_current = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ['-snapshot_date']
        indexes = [
            models.Index(fields=['user', 'symbol', 'is_current']),
        ]


class ResearchMemory(models.Model):
    """
    Research memory tracking user's research activities.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='research_memories')
    
    # Research activity
    activity_type = models.CharField(max_length=30, choices=[
        ('COMPANY_ANALYZED', 'Company Analyzed'),
        ('REPORT_READ', 'Report Read'),
        ('RECOMMENDATION_GENERATED', 'Recommendation Generated'),
        ('QUESTION_ASKED', 'Question Asked'),
        ('DOCUMENT_RETRIEVED', 'Document Retrieved'),
    ])
    
    # Content
    symbol = models.CharField(max_length=20, db_index=True, blank=True)
    company_name = models.CharField(max_length=200, blank=True)
    query = models.TextField(blank=True)
    result_summary = models.TextField(blank=True)
    
    # Context
    session_id = models.CharField(max_length=100, db_index=True)
    documents_used = models.JSONField(default=list, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']


class WatchlistCategory(models.TextChoices):
    WAITING_VALUATION = 'WAITING_VALUATION', 'Waiting for Better Valuation'
    WAITING_EARNINGS = 'WAITING_EARNINGS', 'Waiting for Earnings'
    WAITING_BREAKOUT = 'WAITING_BREAKOUT', 'Waiting for Breakout'
    WAITING_MACRO = 'WAITING_MACRO', 'Waiting for Macro Improvement'
    WAITING_COMPETITOR = 'WAITING_COMPETITOR', 'Waiting for Competitor Update'
    WAITING_TECHNICAL = 'WAITING_TECHNICAL', 'Waiting for Technical Confirmation'


class AIWatchlist(models.Model):
    """
    AI-generated watchlists with intelligent categorization.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_watchlists')
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=30, choices=WatchlistCategory.choices)
    
    # Watchlist items
    symbols = models.JSONField(default=list, blank=True)
    
    # Monitoring configuration
    monitor_price = models.BooleanField(default=True)
    monitor_volume = models.BooleanField(default=True)
    monitor_financials = models.BooleanField(default=True)
    monitor_news = models.BooleanField(default=True)
    monitor_macro = models.BooleanField(default=True)
    monitor_sector = models.BooleanField(default=True)
    monitor_competitors = models.BooleanField(default=True)
    
    # Trigger conditions
    trigger_conditions = models.JSONField(default=dict, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']


class ModelPerformanceMetric(models.Model):
    """
    Track model performance metrics over time for drift detection.
    """
    model_version = models.CharField(max_length=50, db_index=True)
    model_type = models.CharField(max_length=20)
    
    # Performance metrics
    prediction_accuracy = models.FloatField(null=True, blank=True)
    precision = models.FloatField(null=True, blank=True)
    recall = models.FloatField(null=True, blank=True)
    f1_score = models.FloatField(null=True, blank=True)
    rmse = models.FloatField(null=True, blank=True)
    sharpe_ratio = models.FloatField(null=True, blank=True)
    win_rate = models.FloatField(null=True, blank=True)
    average_return = models.FloatField(null=True, blank=True)
    maximum_drawdown = models.FloatField(null=True, blank=True)
    
    # Drift detection
    data_drift_score = models.FloatField(null=True, blank=True)
    concept_drift_score = models.FloatField(null=True, blank=True)
    feature_drift_score = models.FloatField(null=True, blank=True)
    performance_drift_score = models.FloatField(null=True, blank=True)
    prediction_drift_score = models.FloatField(null=True, blank=True)
    
    # Metadata
    evaluation_period_start = models.DateField()
    evaluation_period_end = models.DateField()
    sample_count = models.IntegerField(default=0)
    drift_detected = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['model_version', 'created_at']),
        ]


class AuditLog(models.Model):
    """
    Comprehensive audit logging for all model changes and decisions.
    """
    ACTION_TYPES = [
        ('PREDICTION', 'Prediction'),
        ('RECOMMENDATION', 'Recommendation'),
        ('EXPLANATION', 'Explanation'),
        ('FEEDBACK_RECEIVED', 'Feedback Received'),
        ('MODEL_TRAINED', 'Model Trained'),
        ('MODEL_DEPLOYED', 'Model Deployed'),
        ('MODEL_ARCHIVED', 'Model Archived'),
        ('DRIFT_DETECTED', 'Drift Detected'),
        ('CANDIDATE_CREATED', 'Candidate Created'),
    ]

    model_version = models.CharField(max_length=50, db_index=True)
    action_type = models.CharField(max_length=30, choices=ACTION_TYPES)
    
    # Content
    prediction = models.JSONField(default=dict, blank=True)
    recommendation = models.JSONField(default=dict, blank=True)
    explanation = models.JSONField(default=dict, blank=True)
    user_feedback = models.JSONField(default=dict, blank=True)
    
    # Metadata
    symbol = models.CharField(max_length=20, db_index=True, blank=True)
    user_id = models.IntegerField(null=True, blank=True, db_index=True)
    deployment_date = models.DateTimeField(null=True, blank=True)
    training_dataset = models.CharField(max_length=200, blank=True)
    git_commit = models.CharField(max_length=50, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['model_version', 'action_type', 'created_at']),
        ]


class Alert(models.Model):
    """
    Comprehensive alert system for portfolio, watchlist, and market monitoring.
    """
    ALERT_TYPES = [
        ('PORTFOLIO_RISK', 'Portfolio Risk Alert'),
        ('OPPORTUNITY', 'Opportunity Alert'),
        ('VALUATION', 'Valuation Alert'),
        ('TECHNICAL', 'Technical Alert'),
        ('MACRO', 'Macro Alert'),
        ('NEWS', 'News Alert'),
        ('DIVIDEND', 'Dividend Alert'),
    ]

    ALERT_PRIORITIES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]

    DELIVERY_CHANNELS = [
        ('DASHBOARD', 'Dashboard'),
        ('EMAIL', 'Email'),
        ('PUSH', 'Push Notification'),
        ('WEBSOCKET', 'WebSocket'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPES)
    priority = models.CharField(max_length=10, choices=ALERT_PRIORITIES, default='MEDIUM')
    
    # Alert content
    title = models.CharField(max_length=200)
    message = models.TextField()
    symbol = models.CharField(max_length=20, db_index=True, blank=True)
    company_name = models.CharField(max_length=200, blank=True)
    
    # Trigger details
    trigger_reason = models.TextField(blank=True)
    trigger_data = models.JSONField(default=dict, blank=True)
    
    # Delivery
    delivery_channels = ArrayField(models.CharField(max_length=20), default=list, blank=True)
    delivered = models.BooleanField(default=False)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Actions
    action_taken = models.CharField(max_length=20, blank=True)
    action_taken_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at', '-priority']
        indexes = [
            models.Index(fields=['user', 'read', 'created_at']),
            models.Index(fields=['alert_type', 'priority']),
        ]