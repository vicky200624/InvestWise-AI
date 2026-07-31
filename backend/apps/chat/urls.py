from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatSessionViewSet, ChatMessageView, VoiceChatView

router = DefaultRouter()
router.register(r'sessions', ChatSessionViewSet, basename='chat-session')

urlpatterns = [
    path('', include(router.urls)),
    path('message/', ChatMessageView.as_view(), name='chat-message'),
    path('langchain-chat/', ChatMessageView.as_view(), name='langchain-chat-alias'),
    path('voice-chat/', VoiceChatView.as_view(), name='voice-chat-alias'),
]
