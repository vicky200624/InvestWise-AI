from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AssetHoldingViewSet, PortfolioOptimizeView, PortfolioPerformanceView, DashboardSummaryView

router = DefaultRouter()
router.register(r'holdings', AssetHoldingViewSet, basename='assetholding')

urlpatterns = [
    path('', AssetHoldingViewSet.as_view({'get': 'list', 'post': 'create'}), name='portfolio-root'),
    path('dashboard/', DashboardSummaryView.as_view(), name='dashboard-summary'),
    path('optimize/', PortfolioOptimizeView.as_view(), name='portfolio-optimize'),
    path('performance/', PortfolioPerformanceView.as_view(), name='portfolio-performance'),
    path('', include(router.urls)),
]
