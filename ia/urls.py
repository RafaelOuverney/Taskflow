from django.urls import path
from . import views

urlpatterns = [
    path('config/', views.IAConfigView.as_view(), name='ia_config'),
    path('config/test/', views.IATestConnectionView.as_view(), name='ia_test_connection'),
    path('requisicoes/', views.IARequisicoesView.as_view(), name='ia_requisicoes'),
    path('usuarios/', views.IAConsumoUsuariosView.as_view(), name='ia_usuarios'),
    path('meu-consumo/', views.MeuConsumoView.as_view(), name='ia_meu_consumo'),
    path('assistente/', views.AssistenteView.as_view(), name='ia_assistente'),
    path('assistente/chat/', views.AssistenteChatAPI.as_view(), name='ia_assistente_chat'),
    path('assistente/clear/', views.AssistenteClearHistoryAPI.as_view(), name='ia_assistente_clear'),
]

