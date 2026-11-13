import json
import os
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_protect
from django.views.generic import ListView, TemplateView

from .forms import IAConfigForm
from .models import IAConfig, IACallAudit, UserTokenQuota, ChatMessage, get_current_mes_ano
from .services import chamar_ia


class IAConfigView(LoginRequiredMixin, View):
    """Tela de Configuração da IA (editável) com suporte a Testar Conexão"""
    template_name = "ia/configuracao.html"

    def get(self, request):
        config = IAConfig.get_active_config()
        form = IAConfigForm(instance=config)
        return render(request, self.template_name, {'form': form, 'config': config})

    def post(self, request):
        config = IAConfig.get_active_config()
        form = IAConfigForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, "Configurações de IA atualizadas com sucesso!")
            return redirect('ia_config')
        messages.error(request, "Erro ao salvar as configurações. Verifique os campos.")
        return render(request, self.template_name, {'form': form, 'config': config})


class IATestConnectionView(LoginRequiredMixin, View):
    """Endpoint AJAX para testar a conexão com o provedor de IA configurado"""
    @method_decorator(csrf_protect)
    def post(self, request):
        try:
            result = chamar_ia(
                prompt="Responda com exatamente: 'Conexão com a IA estabelecida com sucesso!'",
                user=request.user,
                endpoint="teste_conexao"
            )
            return JsonResponse(result)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


class IARequisicoesView(LoginRequiredMixin, ListView):
    """Tela de Requisições / Auditoria com DataTables jQuery"""
    model = IACallAudit
    template_name = "ia/requisicoes.html"
    context_object_name = "auditorias"

    def get_queryset(self):
        # Otimiza o carregamento do usuário para evitar queries N+1
        return IACallAudit.objects.select_related('user').all()[:200]


class IAConsumoUsuariosView(LoginRequiredMixin, ListView):
    """Tela de IA por Usuário: monitoramento gerencial de consumo e cotas"""
    model = UserTokenQuota
    template_name = "ia/consumo_usuarios.html"
    context_object_name = "quotas"

    def get_queryset(self):
        mes_ano = get_current_mes_ano()
        # Garante que todos os usuários ativos possuam registro no mês
        for u in User.objects.all():
            UserTokenQuota.get_or_create_for_user(u)
        return UserTokenQuota.objects.filter(mes_ano=mes_ano).select_related('user').order_by('-tokens_used')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mes_ano'] = get_current_mes_ano()
        return context


class MeuConsumoView(LoginRequiredMixin, TemplateView):
    """Tela Meu Consumo: visão pessoal do usuário sobre seu uso e cota mensal"""
    template_name = "ia/meu_consumo.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        quota = UserTokenQuota.get_or_create_for_user(user)
        recent_audits = IACallAudit.objects.filter(user=user)[:15]
        context['quota'] = quota
        context['recent_audits'] = recent_audits
        return context


class AssistenteView(LoginRequiredMixin, TemplateView):
    """Interface moderna do Assistente Virtual integrado ao visual do TaskFlow"""
    template_name = "ia/assistente.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        # Carrega histórico inicial do usuário
        context['historico'] = ChatMessage.objects.filter(user=user).order_by('created_at')
        context['quota'] = UserTokenQuota.get_or_create_for_user(user)
        return context


class AssistenteChatAPI(LoginRequiredMixin, View):
    """
    Endpoint AJAX para o chat do assistente:
    - Proteção CSRF obrigatória
    - Carrega contexto de contexto_projeto.md
    - Mantém janela das últimas 5 mensagens
    - Retorna Markdown para renderização segura
    """
    @method_decorator(csrf_protect)
    def post(self, request):
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '').strip()
            if not user_message:
                return JsonResponse({'success': False, 'error': 'A mensagem não pode estar vazia.'}, status=400)

            # 1. Carrega o contexto do sistema em contexto_projeto.md
            context_path = os.path.join(settings.BASE_DIR, 'contexto_projeto.md')
            system_context = ""
            if os.path.exists(context_path):
                with open(context_path, 'r', encoding='utf-8') as f:
                    system_context = f.read()

            # 2. Busca o histórico do usuário e seleciona exatamente as últimas 5 mensagens (janela de 5)
            ultimas_mensagens = list(
                ChatMessage.objects.filter(user=request.user).order_by('-created_at')[:5]
            )
            ultimas_mensagens.reverse()

            historico_formatado = "\n".join([
                f"{'Usuário' if m.role == 'user' else 'Assistente'}: {m.content}"
                for m in ultimas_mensagens
            ])

            # 3. Monta o prompt contextualizado
            full_prompt = (
                f"--- Histórico recente da conversa (últimas 5 mensagens) ---\n"
                f"{historico_formatado}\n"
                f"--- Fim do histórico ---\n\n"
                f"Usuário: {user_message}\n"
                f"Assistente:"
            )

            # 4. Chama a porta de entrada única da IA
            res = chamar_ia(
                prompt=full_prompt,
                user=request.user,
                endpoint="assistente_chat",
                system_instruction=system_context
            )

            if not res['success']:
                return JsonResponse({'success': False, 'error': res['error']}, status=400)

            # 5. Persiste as mensagens no histórico do banco de dados
            ChatMessage.objects.create(user=request.user, role='user', content=user_message)
            ChatMessage.objects.create(user=request.user, role='assistant', content=res['response'])

            quota = UserTokenQuota.get_or_create_for_user(request.user)

            return JsonResponse({
                'success': True,
                'response': res['response'],
                'total_tokens': res['total_tokens'],
                'tokens_used': quota.tokens_used,
                'monthly_limit': quota.monthly_limit,
                'percentage_used': quota.percentage_used
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': f"Erro no processamento: {str(e)}"}, status=500)


class AssistenteClearHistoryAPI(LoginRequiredMixin, View):
    """Limpa o histórico de conversa do assistente para o usuário atual"""
    @method_decorator(csrf_protect)
    def post(self, request):
        ChatMessage.objects.filter(user=request.user).delete()
        messages.success(request, "Histórico da conversa reiniciado.")
        return JsonResponse({'success': True})

