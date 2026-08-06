from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .services import AgenticWorkflowService

@method_decorator(csrf_exempt, name='dispatch')
class BaseAgenticAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def initial(self, request, *args, **kwargs):
        if 'HTTP_UPGRADE' in request.META:
            del request.META['HTTP_UPGRADE']
        super().initial(request, *args, **kwargs)

    def finalize_response(self, request, response, *args, **kwargs):
        if response.status_code == 426:
            response.status_code = 200
        return super().finalize_response(request, response, *args, **kwargs)


class WorkflowResultView(BaseAgenticAPIView):
    def get(self, request, workflow_id):
        # Pass request.user to map the results to the authenticated user
        data = AgenticWorkflowService.get_results(workflow_id, request.user)
        return Response(data)


class WorkflowExecutionView(BaseAgenticAPIView):
    def get(self, request, workflow_id):
        data = AgenticWorkflowService.get_execution_steps(workflow_id)
        return Response(data)


class WorkflowHistoryView(BaseAgenticAPIView):
    def get(self, request):
        data = AgenticWorkflowService.get_history()
        return Response(data)