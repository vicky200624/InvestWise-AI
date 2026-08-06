from django.urls import path
from .views import AIOperationsDashboardView

app_name = 'ai_operations'

urlpatterns = [
    path('dashboard/', AIOperationsDashboardView.as_view(), name='ai_ops_dashboard'),
]