from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('api/ai-advisor/', views.ai_advisor_view, name='ai_advisor'),
    path('api/tts/', views.tts_view, name='tts'),
    
    # New Asset Detail Pages
    path('stocks/', views.stocks_view, name='stocks'),
    path('mutual-funds/', views.mf_view, name='mutual_funds'),
    path('gold/', views.gold_view, name='gold'),
    path('reits/', views.reits_view, name='reits'),

    # ... your existing paths ...
    path('connect-broker/', views.connect_broker_view, name='connect_broker'),
    path('manual/', views.user_manual_view, name='user_manual'),

    path('chat/', views.chat_ui_view, name='chat'),
path('chat/<uuid:session_id>/', views.chat_ui_view, name='chat_detail'),
path('chat/new/', views.new_chat_session, name='new_chat'),
path('chat/delete/<uuid:session_id>/', views.delete_chat_session, name='delete_chat_session'),
path('api/langchain-chat/', views.langchain_chat_api, name='langchain_chat'),
]