from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AssetHoldingViewSet, PortfolioOptimizeView, PortfolioPerformanceView, DashboardSummaryView, SyncBrokerView

router = DefaultRouter()
router.register(r'holdings', AssetHoldingViewSet, basename='assetholding')

urlpatterns = [
    path('', AssetHoldingViewSet.as_view({'get': 'list', 'post': 'create'}), name='portfolio-root'),
    path('<int:pk>/', AssetHoldingViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='portfolio-detail'),
    path('dashboard/', DashboardSummaryView.as_view(), name='dashboard-summary'),
    path('optimize/', PortfolioOptimizeView.as_view(), name='portfolio-optimize'),
    path('performance/', PortfolioPerformanceView.as_view(), name='portfolio-performance'),
    path('sync-broker/', SyncBrokerView.as_view(), name='portfolio-sync-broker'),
    path('', include(router.urls)),
]


