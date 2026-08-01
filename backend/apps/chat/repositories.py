from django.contrib.auth import get_user_model
User = get_user_model()
from .models import ChatSession, ChatMessage

class ChatRepository:
    @staticmethod
    def get_sessions_by_user(user: User):
        return ChatSession.objects.filter(user=user).order_by('-created_at')
    
    @staticmethod
    def get_session_by_id(session_id: int, user: User):
        try:
            return ChatSession.objects.get(id=session_id, user=user)
        except ChatSession.DoesNotExist:
            return None
    
    @staticmethod
    def get_last_session(user: User):
        return ChatSession.objects.filter(user=user).order_by('-created_at').first()
    
    @staticmethod
    def create_session(user: User, title: str) -> ChatSession:
        return ChatSession.objects.create(user=user, title=title)
    
    @staticmethod
    def create_message(session: ChatSession, user: User, role: str, content: str) -> ChatMessage:
        return ChatMessage.objects.create(session=session, user=user, role=role, content=content)
    
    @staticmethod
    def get_recent_messages(session: ChatSession, limit: int = 7):
        return ChatMessage.objects.filter(session=session).order_by('-timestamp')[:limit]
    
    @staticmethod
    def save_session(session: ChatSession):
        session.save()
        return session
