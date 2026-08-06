from django.db import models
from django.utils import timezone

class LLMTelemetry(models.Model):
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    agent_name = models.CharField(max_length=100)
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    latency_ms = models.FloatField(default=0.0)
    cost = models.FloatField(default=0.0)
    status = models.CharField(max_length=20, default="Success")
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.agent_name} - {self.total_tokens} tokens"