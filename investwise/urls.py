"""
InvestWise AI 3.0 — URL Configuration

Maps all URL patterns to their corresponding view functions.
Includes: auth, dashboard, asset views, chat, AI advisor, voice,
and the new AI analysis engine endpoints.
"""
from django.urls import path
from . import views

urlpatterns = [
    # ==================================================================
    # Authentication
    # ==================================================================
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),

    # ==================================================================
    # Dashboard & Asset Detail Pages
    # ==================================================================
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('stocks/', views.stocks_view, name='stocks'),
    path('mutual-funds/', views.mf_view, name='mutual_funds'),
    path('gold/', views.gold_view, name='gold'),
    path('reits/', views.reits_view, name='reits'),

    # ==================================================================
    # Broker & Manual
    # ==================================================================
    path('connect-broker/', views.connect_broker_view, name='connect_broker'),
    path('manual/', views.user_manual_view, name='user_manual'),

    # ==================================================================
    # Chat Interface (LangChain RAG)
    # ==================================================================
    path('chat/', views.chat_ui_view, name='chat'),
    path('chat/<uuid:session_id>/', views.chat_ui_view, name='chat_detail'),
    path('chat/new/', views.new_chat_session, name='new_chat'),
    path('chat/delete/<uuid:session_id>/', views.delete_chat_session, name='delete_chat_session'),
    path('api/langchain-chat/', views.langchain_chat_api, name='langchain_chat'),

    # ==================================================================
    # AI Advisor & Voice (Existing)
    # ==================================================================
    path('api/ai-advisor/', views.ai_advisor_view, name='ai_advisor'),
    path('api/tts/', views.tts_view, name='tts'),
    path('api/voice-chat/', views.voice_chat_api, name='voice_chat_api'),

    # ==================================================================
    # AI 3.0 — Analysis Engine (NEW)
    # ==================================================================
    path('analysis/', views.analysis_view, name='analysis'),
    path('api/analysis/run/', views.run_analysis_api, name='run_analysis'),
    path('api/analysis/status/<uuid:task_id>/', views.analysis_status_api, name='analysis_status'),
    path('api/analysis/result/<int:analysis_id>/', views.analysis_result_api, name='analysis_result'),
    path('api/analysis/history/', views.analysis_history_api, name='analysis_history'),

    # ==================================================================
    # AI 3.0 — RLHF Feedback (NEW)
    # ==================================================================
    path('api/feedback/', views.investment_feedback_api, name='investment_feedback'),

    # ==================================================================
    # AI 3.0 — Portfolio Optimization (NEW)
    # ==================================================================
    path('api/portfolio/optimize/', views.portfolio_optimize_api, name='portfolio_optimize'),
]