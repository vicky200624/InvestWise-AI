from django.contrib.auth.models import User
from .models import ChatSession, ChatMessage

class ChatService:
    @staticmethod
    def process_message(user: User, session_id: int, content: str) -> dict:
        try:
            session = ChatSession.objects.get(id=session_id, user=user)
        except ChatSession.DoesNotExist:
            return {'error': 'Session not found'}

        # Save user message
        ChatMessage.objects.create(session=session, user=user, role='user', content=content)

        # Mock LangChain RAG invocation
        ai_response_content = "This is a mocked AI response based on LangChain RAG."
        
        # Save AI response
        ai_message = ChatMessage.objects.create(
            session=session, 
            user=user, 
            role='ai', 
            content=ai_response_content
        )

        return {
            'session_id': session.id,
            'message': ai_message.content,
            'role': ai_message.role,
            'timestamp': ai_message.timestamp
        }
