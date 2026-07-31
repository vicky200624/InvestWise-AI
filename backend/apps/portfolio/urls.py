from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AssetHoldingViewSet, PortfolioOptimizeView, PortfolioPerformanceView

router = DefaultRouter()
router.register(r'holdings', AssetHoldingViewSet, basename='assetholding')

urlpatterns = [
    path('', include(router.urls)),
    path('optimize/', PortfolioOptimizeView.as_view(), name='portfolio-optimize'),
    path('performance/', PortfolioPerformanceView.as_view(), name='portfolio-performance'),
]
