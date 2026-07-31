from rest_framework import viewsets, views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import ChatSession
from .serializers import ChatSessionSerializer
from .services import ChatService
from core.permissions import IsOwner

class ChatSessionViewSet(viewsets.ModelViewSet):
    serializer_class = ChatSessionSerializer
    permission_classes = (IsAuthenticated, IsOwner)

    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user).order_by('-created_at')

class ChatMessageView(views.APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        session_id = request.data.get('session_id')
        content = request.data.get('content')
        
        if not session_id or not content:
            return Response({'error': 'session_id and content are required'}, status=status.HTTP_400_BAD_REQUEST)
            
        result = ChatService.process_message(request.user, session_id, content)
        if 'error' in result:
            return Response(result, status=status.HTTP_404_NOT_FOUND)
            
        return Response(result)
