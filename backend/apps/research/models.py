import uuid
from django.db import models
from django.contrib.auth.models import User

class StockAnalysis(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analyses')
    stock_symbol = models.CharField(max_length=20, db_index=True)
    stock_name = models.CharField(max_length=200, blank=True)
    time_horizon = models.CharField(max_length=10, choices=[('SHORT', 'Short-term'), ('LONG', 'Long-term')])
    investment_score = models.FloatField(null=True, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    recommendation = models.CharField(max_length=20, blank=True)
    fundamental_score = models.FloatField(null=True, blank=True)
    quant_score = models.FloatField(null=True, blank=True)
    sentiment_score = models.FloatField(null=True, blank=True)
    fundamental_data = models.JSONField(default=dict, blank=True)
    quant_data = models.JSONField(default=dict, blank=True)
    sentiment_data = models.JSONField(default=dict, blank=True)
    shap_values = models.JSONField(default=dict, blank=True)
    top_factors = models.JSONField(default=list, blank=True)
    nn_model_used = models.CharField(max_length=20, blank=True)
    predicted_price = models.FloatField(null=True, blank=True)
    current_price = models.FloatField(null=True, blank=True)
    prediction_horizon_days = models.IntegerField(null=True, blank=True)
    portfolio_suggestion = models.JSONField(default=dict, blank=True)
    processing_time_seconds = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

class AgentTask(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='agent_tasks')
    task_type = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=[
        ('PENDING','Pending'),
        ('RUNNING','Running'),
        ('COMPLETED','Completed'),
        ('FAILED','Failed'),
        ('CANCELLED','Cancelled')
    ], default='PENDING', db_index=True)
    progress_percent = models.IntegerField(default=0)
    current_step = models.CharField(max_length=255, blank=True)
    celery_task_id = models.CharField(max_length=255, blank=True)
    input_data = models.JSONField(default=dict, blank=True)
    result_data = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

class RAGDocument(models.Model):
    stock_symbol = models.CharField(max_length=20, db_index=True)
    source_type = models.CharField(max_length=20, choices=[
        ('10K','10-K Filing'),
        ('10Q','10-Q Filing'),
        ('EARNINGS','Earnings Call'),
        ('NEWS','News Article'),
        ('CUSTOM','Custom')
    ])
    title = models.CharField(max_length=500)
    source_url = models.URLField(max_length=1000, blank=True)
    chromadb_collection = models.CharField(max_length=100)
    chunk_count = models.IntegerField(default=0)
    ingested_at = models.DateTimeField(auto_now_add=True)

class InvestmentFeedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    analysis = models.ForeignKey(StockAnalysis, on_delete=models.CASCADE, related_name='feedback')
    feedback_type = models.CharField(max_length=20)
    comment = models.TextField(blank=True)
    reward_signal = models.FloatField(null=True, blank=True)
    actual_outcome = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class TrainedModel(models.Model):
    symbol = models.CharField(max_length=20, db_index=True)
    model_type = models.CharField(max_length=20, choices=[
        ('LSTM','LSTM'),
        ('GRU','GRU'),
        ('FNN','FNN'),
        ('XGBOOST','XGBoost'),
        ('CATBOOST','CatBoost')
    ])
    version = models.CharField(max_length=50)
    file_path = models.CharField(max_length=500)
    is_active = models.BooleanField(default=False, db_index=True)
    metrics = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class MacroIndicator(models.Model):
    indicator_code = models.CharField(max_length=20)
    indicator_name = models.CharField(max_length=200)
    date = models.DateField()
    value = models.FloatField()
    source = models.CharField(max_length=20, default='FRED')
