from django.db import models
from django.utils import timezone

class AgenticWorkflowRun(models.Model):
    workflow_id = models.CharField(max_length=100)
    status = models.CharField(max_length=50, default="Completed")
    risk_score = models.CharField(max_length=20)
    confidence = models.CharField(max_length=20)
    expected_return = models.CharField(max_length=20)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    def __str__(self):
        return f"{self.workflow_id} - {self.status} ({self.created_at})"