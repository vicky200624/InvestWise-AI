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
        content = request.data.get('content') or request.data.get('message')
        
        if not content:
            return Response({'error': 'message or content is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        if not session_id:
            session = ChatSession.objects.filter(user=request.user).order_by('-created_at').first()
            if not session:
                session = ChatSession.objects.create(user=request.user, title="New Conversation")
            session_id = session.id

        result = ChatService.process_message(request.user, session_id, content)
        if 'error' in result:
            return Response(result, status=status.HTTP_404_NOT_FOUND)
            
        return Response(result, status=status.HTTP_200_OK)

class VoiceChatView(views.APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        audio_file = request.FILES.get('audio')
        user_text = request.data.get('user_text') or request.data.get('message')
        
        if not audio_file and not user_text:
            return Response({"error": "Audio file or user_text required."}, status=status.HTTP_400_BAD_REQUEST)

        text_input = user_text or "Voice input message"
        session = ChatSession.objects.filter(user=request.user).order_by('-created_at').first()
        if not session:
            session = ChatSession.objects.create(user=request.user, title="Voice Conversation")

        result = ChatService.process_message(request.user, session.id, text_input)
        
        return Response({
            "user_text": text_input,
            "ai_text": result.get("message", "Processed voice message."),
            "audio_base64": ""
        }, status=status.HTTP_200_OK)
