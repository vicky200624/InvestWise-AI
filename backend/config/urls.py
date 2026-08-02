from django.contrib import admin
from django.urls import path, include
from core.health import health_check, readiness_check, liveness_check
from apps.portfolio.views import DashboardSummaryView, PortfolioOptimizeView
from apps.research.views import AnalyzeStockView
from apps.chat.views import ChatMessageView, VoiceChatView

urlpatterns = [
    path('admin/', admin.site.urls),
    # Health check endpoints
    path('api/v1/health/', health_check, name='health_check'),
    path('api/v1/health/ready/', readiness_check, name='readiness_check'),
    path('api/v1/health/alive/', liveness_check, name='liveness_check'),
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/portfolio/', include('apps.portfolio.urls')),
    path('api/v1/research/', include('apps.research.urls')),
    path('api/v1/chat/', include('apps.chat.urls')),
    path('api/v1/watchlist/', include('apps.watchlist.urls')),
    # Canonical direct /api/ aliases required by frontend integration
    path('api/dashboard/', DashboardSummaryView.as_view(), name='api-dashboard-summary'),
    path('api/portfolio/', include('apps.portfolio.urls')),
    path('api/research/', include('apps.research.urls')),
    path('api/watchlist/', include('apps.watchlist.urls')),
    path('api/chat/', include('apps.chat.urls')),
    # Direct legacy aliases
    path('api/langchain-chat/', ChatMessageView.as_view(), name='legacy-langchain-chat'),
    path('api/voice-chat/', VoiceChatView.as_view(), name='legacy-voice-chat'),
    path('api/analysis/run/', AnalyzeStockView.as_view(), name='legacy-analysis-run'),
    path("api/accounts/", include("apps.accounts.urls")),
    path('api/portfolio/optimize/', PortfolioOptimizeView.as_view(), name='legacy-portfolio-optimize'),
]