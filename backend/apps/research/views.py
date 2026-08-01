from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import StockAnalysis, AgentTask, InvestmentFeedback
from .serializers import StockAnalysisSerializer, AgentTaskSerializer, InvestmentFeedbackSerializer
from .services import ResearchService
from .repositories import ResearchRepository
from core.permissions import IsOwner

class StockAnalysisViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StockAnalysisSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        return ResearchRepository.get_analyses_by_user(self.request.user)

class AgentTaskViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AgentTaskSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        return ResearchRepository.get_tasks_by_user(self.request.user)

class AnalyzeStockView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        symbol = request.data.get('stock_symbol') or request.data.get('symbol')
        horizon = request.data.get('time_horizon', 'LONG')
        if not symbol:
            return Response({'error': 'symbol or stock_symbol is required'}, status=status.HTTP_400_BAD_REQUEST)

        result = ResearchService.trigger_analysis(request.user, symbol, horizon)
        return Response(result, status=status.HTTP_200_OK)

class SubmitFeedbackView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        analysis_id = request.data.get('analysis')
        f_type = request.data.get('feedback_type')
        comment = request.data.get('comment', '')
        if not analysis_id or not f_type:
            return Response({'error': 'analysis and feedback_type are required'}, status=status.HTTP_400_BAD_REQUEST)

        result = ResearchService.submit_feedback(request.user, analysis_id, f_type, comment)
        return Response(result, status=status.HTTP_200_OK)
