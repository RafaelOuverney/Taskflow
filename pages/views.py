import json

from django.http import JsonResponse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.contrib.auth import login, authenticate, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.models import User

class IndexView(TemplateView):
    template_name = 'index.html'
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, 'index.html')
    
    @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            email = data.get('email', '').strip()
            password = data.get('password', '')
            remember_me = data.get('rememberMe', False)

            if not email or not password:
                return JsonResponse({
                    'success': False,
                    'message': 'Email e senha são obrigatórios.'
                }, status=400)
            
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                if remember_me:
                    request.session.set_expiry(1209600) 
                    request.session['remember_me'] = True
                else:
                    request.session.set_expiry(0) 
                    request.session['remember_me'] = False

                return JsonResponse({
                    'success': True,
                    'message': 'Login realizado com sucesso! Redirecionando...',
                    'redirect': '/dashboard/'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Credenciais inválidas. Tente novamente.'
                }, status=401)
        
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao processar login: {str(e)}'
            }, status=500)


class RecuperacaoView(TemplateView):
    template_name = 'recuperacao.html'
    
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CadastroView(TemplateView):
    template_name = 'cadastro.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, 'cadastro.html')
    
    @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            full_name = data.get('fullName', '').strip()
            email = data.get('email', '').strip()
            password = data.get('password', '')
            confirm_password = data.get('confirmPassword', '')
            terms = data.get('terms', False)

            if not all([full_name, email, password, confirm_password]):
                return JsonResponse({
                    'success': False,
                    'message': 'Todos os campos são obrigatórios.'
                }, status=400)
            
            if len(full_name) < 3:
                return JsonResponse({
                    'success': False,
                    'message': 'O nome completo deve conter pelo menos 3 caracteres.'
                }, status=400)
            
            if password != confirm_password:
                return JsonResponse({
                    'success': False,
                    'message': 'As senhas não coincidem.'
                }, status=400)
            
            if not terms:
                return JsonResponse({
                    'success': False,
                    'message': 'Você deve aceitar os termos e condições.'
                }, status=400)
            
            if User.objects.filter(email=email).exists() or User.objects.filter(username=email).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Este email já está registrado.'
                }, status=400)
            
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=full_name.split()[0],
                last_name=' '.join(full_name.split()[1:]) if len(full_name.split()) > 1 else ''
            )

            login(request, user)

            return JsonResponse({
                'success': True,
                'message': 'Cadastro realizado com sucesso! Redirecionando...',
                'redirect': '/dashboard/'
            })
        
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao processar cadastro: {str(e)}'
            }, status=500)
        
class LogoutView(TemplateView):
    template_name = 'index.html'

    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect('index')
    
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'
    login_url = 'index'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_name'] = self.request.user.first_name or self.request.user.email
        return context

class NotebookListView(LoginRequiredMixin, TemplateView):
    template_name = 'caderno.html'
    login_url = 'index'
    
    def get_context_data(self, **kwargs):
        from .models import Notebook
        context = super().get_context_data(**kwargs)
        
        notebook_id = self.kwargs.get('notebook_id')
        if notebook_id:
            try:
                notebook = Notebook.objects.get(id=notebook_id, owner=self.request.user)
                context['notebook'] = notebook
            except Notebook.DoesNotExist:
                context['notebook'] = None
        else:
            latest = Notebook.objects.filter(owner=self.request.user).first()
            context['notebook'] = latest
        
        context['notebooks'] = Notebook.objects.filter(owner=self.request.user)
        return context


class NotebookCreateAPI(LoginRequiredMixin, TemplateView):
    @method_decorator(csrf_protect)
    def post(self, request):
        from .models import Notebook
        try:
            data = json.loads(request.body)
            title = data.get('title', 'Novo Caderno').strip()
            
            notebook = Notebook.objects.create(
                title=title,
                owner=request.user,
                content=''
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Caderno criado com sucesso!',
                'notebook': {
                    'id': notebook.id,
                    'title': notebook.title,
                    'content': notebook.content
                }
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao criar caderno: {str(e)}'
            }, status=500)


class NotebookSaveAPI(LoginRequiredMixin, TemplateView):
    @method_decorator(csrf_protect)
    def post(self, request):
        from .models import Notebook
        try:
            data = json.loads(request.body)
            notebook_id = data.get('notebook_id')
            title = data.get('title', '').strip()
            content = data.get('content', '')
            
            notebook = Notebook.objects.get(id=notebook_id, owner=request.user)
            notebook.title = title
            notebook.content = content
            notebook.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Caderno salvo com sucesso!',
                'updated_at': notebook.updated_at.strftime('%d/%m/%Y %H:%M')
            })
        except Notebook.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Caderno não encontrado.'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao salvar caderno: {str(e)}'
            }, status=500)


class NotebookDeleteAPI(LoginRequiredMixin, TemplateView):
    @method_decorator(csrf_protect)
    def post(self, request):
        from .models import Notebook
        try:
            data = json.loads(request.body)
            notebook_id = data.get('notebook_id')
            
            notebook = Notebook.objects.get(id=notebook_id, owner=request.user)
            notebook.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Caderno deletado com sucesso!'
            })
        except Notebook.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Caderno não encontrado.'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao deletar caderno: {str(e)}'
            }, status=500)


class NotebookGetListAPI(LoginRequiredMixin, TemplateView):
    def get(self, request):
        from .models import Notebook
        try:
            notebooks = Notebook.objects.filter(owner=request.user).values(
                'id', 'title', 'updated_at'
            )
            
            return JsonResponse({
                'success': True,
                'notebooks': list(notebooks)
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao buscar cadernos: {str(e)}'
            }, status=500)
        

