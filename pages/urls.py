from django.urls import path
from .views import IndexView, RecuperacaoView, CadastroView


urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('recuperacao/', RecuperacaoView.as_view(), name='recuperacao'),
    path('cadastro/', CadastroView.as_view(), name='cadastro'),
]