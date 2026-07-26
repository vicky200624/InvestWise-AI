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
]