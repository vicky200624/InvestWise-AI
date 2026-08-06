from django.urls import path
from .views import WorkflowResultView, WorkflowExecutionView, WorkflowHistoryView

app_name = 'agentic_ai'

urlpatterns = [
    path('result/<str:workflow_id>/', WorkflowResultView.as_view(), name='workflow_result'),
    path('execution/<str:workflow_id>/', WorkflowExecutionView.as_view(), name='workflow_execution'),
    path('history/', WorkflowHistoryView.as_view(), name='workflow_history'),
]