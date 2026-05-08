from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect

class IndexView(TemplateView):
    template_name = 'index.html'
    
    def get(self, request, *args, **kwargs):
        # If user is already logged in, redirect to dashboard
        # (Uncomment this when you have a dashboard view)
        # if request.user.is_authenticated:
        #     return redirect('dashboard')
        
        return super().get(request, *args, **kwargs)


class RecuperacaoView(TemplateView):
    template_name = 'recuperacao.html'
    
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CadastroView(TemplateView):
    template_name = 'cadastro.html'
    
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)