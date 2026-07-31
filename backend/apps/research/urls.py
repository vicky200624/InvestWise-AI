from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StockAnalysisViewSet, AgentTaskViewSet, AnalyzeStockView, SubmitFeedbackView

router = DefaultRouter()
router.register(r'history', StockAnalysisViewSet, basename='stockanalysis')
router.register(r'tasks', AgentTaskViewSet, basename='agenttask')

urlpatterns = [
    path('', include(router.urls)),
    path('analyze/', AnalyzeStockView.as_view(), name='research-analyze'),
    path('feedback/', SubmitFeedbackView.as_view(), name='research-feedback'),
]
