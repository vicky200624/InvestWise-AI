from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import AssetHolding
from .serializers import AssetHoldingSerializer
from .services import PortfolioService
from core.permissions import IsOwner

class AssetHoldingViewSet(viewsets.ModelViewSet):
    serializer_class = AssetHoldingSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        return AssetHolding.objects.filter(user=self.request.user)

class PortfolioOptimizeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        symbols = request.data.get('symbols', None)
        method = request.data.get('method', 'markowitz')
        result = PortfolioService.optimize_portfolio(request.user, method=method, symbols=symbols)
        return Response(result, status=status.HTTP_200_OK)

class PortfolioPerformanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        result = PortfolioService.get_performance(request.user)
        return Response(result, status=status.HTTP_200_OK)

class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        result = PortfolioService.get_dashboard_summary(request.user)
        return Response(result, status=status.HTTP_200_OK)

class SyncBrokerView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        result = PortfolioService.sync_broker_holdings(request.user)
        status_code = status.HTTP_200_OK if result.get('status') == 'success' else status.HTTP_400_BAD_REQUEST
        return Response(result, status=status_code)

