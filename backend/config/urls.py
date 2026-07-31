from django.contrib import admin
from django.urls import path, include
from core.health import HealthCheckView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/health/', HealthCheckView.as_view(), name='health-check'),
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/portfolio/', include('apps.portfolio.urls')),
    path('api/v1/research/', include('apps.research.urls')),
    path('api/v1/chat/', include('apps.chat.urls')),
    path('api/v1/watchlist/', include('apps.watchlist.urls')),
]

