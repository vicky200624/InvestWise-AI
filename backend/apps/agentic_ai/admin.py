from django.contrib import admin
from .models import AgenticWorkflowRun

@admin.register(AgenticWorkflowRun)
class AgenticWorkflowRunAdmin(admin.ModelAdmin):
    list_display = ('workflow_id', 'status', 'risk_score', 'confidence', 'expected_return', 'created_at')
    search_fields = ('workflow_id', 'status')