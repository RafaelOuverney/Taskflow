from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


def get_current_mes_ano():
    now = timezone.now()
    return f"{now.year}-{now.month:02d}"


class IAConfig(models.Model):
    """Configuração editável da IA (Singleton com suporte a tela de configuração)"""
    PROVIDER_CHOICES = [
        ('gemini', 'Google Gemini'),
        ('openai', 'OpenAI'),
        ('custom', 'Custom / Outro'),
    ]

    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default='gemini', verbose_name="Provedor")
    model_name = models.CharField(max_length=100, default='gemini-2.5-flash', verbose_name="Nome do Modelo")
    api_key = models.CharField(max_length=255, blank=True, default='', verbose_name="Chave de API")
    endpoint_url = models.URLField(blank=True, default='', verbose_name="Endpoint Customizado (Opcional)")
    temperature = models.FloatField(default=0.7, verbose_name="Temperatura")
    max_tokens = models.PositiveIntegerField(default=2048, verbose_name="Limite Máximo de Tokens por Resposta")
    system_prompt = models.TextField(
        blank=True, 
        default="Você é o assistente virtual inteligente e prestativo do TaskFlow. Ajude os usuários a organizarem suas tarefas, notas e equipes.",
        verbose_name="Prompt Padrão do Sistema"
    )
    ativo = models.BooleanField(default=True, verbose_name="IA Habilitada no Sistema")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuração de IA"
        verbose_name_plural = "Configurações de IA"

    def __str__(self):
        status = "Ativo" if self.ativo else "Inativo"
        return f"{self.get_provider_display()} ({self.model_name}) - {status}"

    @classmethod
    def get_active_config(cls):
        config, created = cls.objects.get_or_create(id=1)
        return config


class UserTokenQuota(models.Model):
    """Cota mensal de tokens por usuário"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ia_quotas', verbose_name="Usuário")
    mes_ano = models.CharField(max_length=7, default=get_current_mes_ano, verbose_name="Mês/Ano de Referência")
    monthly_limit = models.PositiveIntegerField(default=50000, verbose_name="Cota Mensal (Tokens)")
    tokens_used = models.PositiveIntegerField(default=0, verbose_name="Tokens Utilizados no Mês")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cota de Tokens do Usuário"
        verbose_name_plural = "Cotas de Tokens dos Usuários"
        unique_together = ('user', 'mes_ano')
        ordering = ['-mes_ano', 'user']

    def __str__(self):
        return f"{self.user.username} ({self.mes_ano}): {self.tokens_used}/{self.monthly_limit} tokens"

    @property
    def percentage_used(self):
        if not self.monthly_limit or self.monthly_limit == 0:
            return 100
        return min(100, round((self.tokens_used / self.monthly_limit) * 100))

    @property
    def remaining_tokens(self):
        return max(0, self.monthly_limit - self.tokens_used)

    @classmethod
    def get_or_create_for_user(cls, user):
        mes_ano = get_current_mes_ano()
        quota, created = cls.objects.get_or_create(
            user=user,
            mes_ano=mes_ano,
            defaults={'monthly_limit': 50000, 'tokens_used': 0}
        )
        return quota


class IACallAudit(models.Model):
    """Auditoria detalhada de cada requisição realizada à IA"""
    STATUS_CHOICES = [
        ('success', 'Sucesso'),
        ('error', 'Erro'),
        ('quota_exceeded', 'Cota Excedida'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ia_audits', verbose_name="Usuário")
    endpoint = models.CharField(max_length=100, default='assistente', verbose_name="Origem/Endpoint")
    model_used = models.CharField(max_length=100, default='gemini-2.5-flash', verbose_name="Modelo Utilizado")
    prompt = models.TextField(verbose_name="Prompt de Entrada")
    response = models.TextField(blank=True, default='', verbose_name="Resposta Gerada")
    prompt_tokens = models.PositiveIntegerField(default=0, verbose_name="Tokens do Prompt")
    response_tokens = models.PositiveIntegerField(default=0, verbose_name="Tokens da Resposta")
    total_tokens = models.PositiveIntegerField(default=0, verbose_name="Total de Tokens")
    latency_ms = models.PositiveIntegerField(default=0, verbose_name="Latência (ms)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='success', verbose_name="Status")
    error_message = models.TextField(blank=True, default='', verbose_name="Mensagem de Erro")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data/Hora")

    class Meta:
        verbose_name = "Auditoria de Chamada à IA"
        verbose_name_plural = "Auditorias de Chamadas à IA"
        ordering = ['-created_at']

    def __str__(self):
        u = self.user.username if self.user else "Anônimo"
        return f"[{self.created_at.strftime('%d/%m/%Y %H:%M')}] {u} - {self.status} ({self.total_tokens} tok)"


class ChatMessage(models.Model):
    """Mensagens do histórico de conversa com o assistente por usuário"""
    ROLE_CHOICES = [
        ('user', 'Usuário'),
        ('assistant', 'Assistente'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.user.username} ({self.role}): {self.content[:30]}..."

