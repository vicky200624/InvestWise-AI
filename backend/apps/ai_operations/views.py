from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .services import AIOperationsService

class AIOperationsDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # We delegate all data gathering to the Service layer to keep views clean
        data = AIOperationsService.get_dashboard_data()
        return Response(data)