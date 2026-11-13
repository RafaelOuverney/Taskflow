"""Testes caixa-branca para todos os caminhos de controle do módulo ia (models, forms, services, views)."""

import json
from datetime import timedelta
from unittest.mock import MagicMock, patch

import requests
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.utils import timezone

from ia.forms import IAConfigForm, UserQuotaUpdateForm
from ia.models import ChatMessage, IACallAudit, IAConfig, UserTokenQuota, get_current_mes_ano
from ia.services import chamar_ia, estimate_tokens


class IAModelsAndFormsWhiteBoxTests(TestCase):
    """Cobre propriedades de cota, singleton IAConfig, strings de auditoria e formulários de ia."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(username="ia_user@taskflow.com", password="Password@123")

    def test_quota_properties_and_singleton(self) -> None:
        """Verifica get_active_config, percentage_used (incluindo limite 0) e remaining_tokens."""
        cfg = IAConfig.get_active_config()
        self.assertEqual(cfg.id, 1)
        self.assertIn("Ativo", str(cfg))

        quota = UserTokenQuota.get_or_create_for_user(self.user)
        self.assertEqual(quota.mes_ano, get_current_mes_ano())
        quota.monthly_limit = 1000
        quota.tokens_used = 250
        self.assertEqual(quota.percentage_used, 25)
        self.assertEqual(quota.remaining_tokens, 750)

        quota.monthly_limit = 0
        self.assertEqual(quota.percentage_used, 100)
        self.assertEqual(quota.remaining_tokens, 0)
        self.assertIn(self.user.username, str(quota))

        audit_anon = IACallAudit.objects.create(prompt="Teste", status="success")
        self.assertIn("Anônimo", str(audit_anon))
        msg = ChatMessage.objects.create(user=self.user, role="user", content="Olá assistente")
        self.assertIn("Olá assistente", str(msg))

    def test_ia_forms(self) -> None:
        """Valida IAConfigForm e UserQuotaUpdateForm."""
        cfg = IAConfig.get_active_config()
        f_cfg = IAConfigForm(
            data={
                "provider": "gemini",
                "model_name": "gemini-2.5-flash",
                "temperature": 0.5,
                "max_tokens": 1024,
                "system_prompt": "Ajude",
                "ativo": True,
            },
            instance=cfg,
        )
        self.assertTrue(f_cfg.is_valid())
        f_quota = UserQuotaUpdateForm(data={"monthly_limit": 10000})
        self.assertTrue(f_quota.is_valid())


class IAServicesControlFlowWhiteBoxTests(TestCase):
    """Cobre todos os ramos de controle de chamar_ia() e estimate_tokens()."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(username="ia_flow@taskflow.com", password="Password@123")
        self.cfg = IAConfig.get_active_config()

    def test_estimate_tokens_boundaries(self) -> None:
        self.assertEqual(estimate_tokens(""), 0)
        self.assertEqual(estimate_tokens("ab"), 1)
        self.assertEqual(estimate_tokens("12345678"), 2)

    def test_ia_disabled_path(self) -> None:
        """Caminho 1: IA desativada retorna erro imediato sem criar auditoria."""
        self.cfg.ativo = False
        self.cfg.save()
        res = chamar_ia("Oi", self.user)
        self.assertFalse(res["success"])
        self.assertEqual(IACallAudit.objects.count(), 0)

    def test_quota_exceeded_path(self) -> None:
        """Caminho 2: Cota mensal esgotada bloqueia chamada e registra auditoria quota_exceeded."""
        quota = UserTokenQuota.get_or_create_for_user(self.user)
        quota.tokens_used = quota.monthly_limit
        quota.save()

        res = chamar_ia("Oi", self.user)
        self.assertFalse(res["success"])
        self.assertEqual(IACallAudit.objects.filter(status="quota_exceeded").count(), 1)

    def test_gemini_fallback_without_api_key(self) -> None:
        """Caminho 3: Gemini sem API Key gera resposta simulada, registra auditoria e debita cota."""
        self.cfg.provider = "gemini"
        self.cfg.api_key = ""
        self.cfg.save()

        res = chamar_ia("Como organizar minhas tarefas?", self.user, endpoint="teste")
        self.assertTrue(res["success"])
        self.assertIn("chave de API", res["response"])
        quota = UserTokenQuota.get_or_create_for_user(self.user)
        self.assertGreater(quota.tokens_used, 0)

    @patch("ia.services.requests.post")
    def test_gemini_http_success_and_http_error(self, mock_post: MagicMock) -> None:
        """Caminho 4: Gemini com API Key (HTTP 200 com usageMetadata vs HTTP 429)."""
        self.cfg.provider = "gemini"
        self.cfg.api_key = "fake-gemini-key"
        self.cfg.save()

        mock_ok = MagicMock(status_code=200)
        mock_ok.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "Resposta Gemini"}]}}],
            "usageMetadata": {"promptTokenCount": 12, "candidatesTokenCount": 8},
        }
        mock_post.return_value = mock_ok

        res_ok = chamar_ia("Olá", self.user)
        self.assertTrue(res_ok["success"])
        self.assertEqual(res_ok["response"], "Resposta Gemini")
        self.assertEqual(res_ok["total_tokens"], 20)

        mock_err = MagicMock(status_code=429, text="Rate limit")
        mock_post.return_value = mock_err
        res_err = chamar_ia("Olá", self.user)
        self.assertFalse(res_err["success"])
        self.assertIn("429", res_err["error"])

    @patch("ia.services.requests.post")
    def test_openai_and_custom_and_exceptions(self, mock_post: MagicMock) -> None:
        """Caminhos 5, 6, 7 e 8: OpenAI (sem chave / 200 / erro), Custom e RequestException."""
        # OpenAI sem chave
        self.cfg.provider = "openai"
        self.cfg.api_key = ""
        self.cfg.save()
        res_no_key = chamar_ia("Oi", self.user)
        self.assertTrue(res_no_key["success"])
        self.assertIn("OpenAI", res_no_key["response"])

        # OpenAI HTTP 200 e HTTP 500
        self.cfg.api_key = "fake-openai-key"
        self.cfg.save()
        mock_ok = MagicMock(status_code=200)
        mock_ok.json.return_value = {
            "choices": [{"message": {"content": "Resposta OpenAI"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }
        mock_post.return_value = mock_ok
        res_oa_ok = chamar_ia("Oi", self.user)
        self.assertTrue(res_oa_ok["success"])
        self.assertEqual(res_oa_ok["total_tokens"], 15)

        mock_post.return_value = MagicMock(status_code=500, text="Internal Error")
        res_oa_err = chamar_ia("Oi", self.user)
        self.assertFalse(res_oa_err["success"])

        # Custom provider
        self.cfg.provider = "custom"
        self.cfg.save()
        res_custom = chamar_ia("Oi", self.user)
        self.assertTrue(res_custom["success"])
        self.assertIn("customizado", res_custom["response"])

        # Exceção de rede
        self.cfg.provider = "gemini"
        self.cfg.api_key = "fake-key"
        self.cfg.save()
        mock_post.side_effect = requests.exceptions.Timeout("timeout simulado")
        res_exc = chamar_ia("Oi", self.user)
        self.assertFalse(res_exc["success"])
        self.assertIn("Exceção de rede", res_exc["error"])


class IAViewsWhiteBoxTests(TestCase):
    """Cobre todas as views e APIs do app ia, incluindo janela de 5 mensagens e isolamento de histórico."""

    def setUp(self) -> None:
        self.alice = User.objects.create_user(username="alice_ia@taskflow.com", password="Password@123")
        self.bob = User.objects.create_user(username="bob_ia@taskflow.com", password="Password@123")
        self.client_alice = Client()
        self.client_alice.force_login(self.alice)

    def test_config_requisicoes_consumo_views(self) -> None:
        """Verifica IAConfigView (GET/POST), IATestConnectionView, IARequisicoesView, IAConsumoUsuariosView e MeuConsumoView."""
        self.assertEqual(self.client_alice.get("/ia/config/").status_code, 200)
        resp_post = self.client_alice.post(
            "/ia/config/",
            {
                "provider": "gemini",
                "model_name": "gemini-2.5-flash",
                "temperature": "0.6",
                "max_tokens": "1024",
                "system_prompt": "Sistema",
                "ativo": "on",
            },
        )
        self.assertEqual(resp_post.status_code, 302)

        resp_test = self.client_alice.post("/ia/config/test/")
        self.assertEqual(resp_test.status_code, 200)
        self.assertTrue(resp_test.json()["success"])

        self.assertEqual(self.client_alice.get("/ia/requisicoes/").status_code, 200)
        self.assertEqual(self.client_alice.get("/ia/usuarios/").status_code, 200)
        self.assertEqual(self.client_alice.get("/ia/meu-consumo/").status_code, 200)

    def test_assistente_chat_window_and_clear_isolation(self) -> None:
        """Verifica janela de 5 mensagens no AssistenteChatAPI e isolamento ao limpar histórico."""
        self.assertEqual(self.client_alice.get("/ia/assistente/").status_code, 200)

        # Mensagem vazia -> 400
        self.assertEqual(
            self.client_alice.post("/ia/assistente/chat/", data=json.dumps({"message": "  "}), content_type="application/json").status_code,
            400,
        )

        # Cria 7 mensagens antigas para Alice com timestamps distintos e 1 para Bob
        base_dt = timezone.now() - timedelta(minutes=10)
        for i in range(7):
            m = ChatMessage.objects.create(user=self.alice, role="user", content=f"Msg antiga {i}")
            ChatMessage.objects.filter(id=m.id).update(created_at=base_dt + timedelta(seconds=i))
        ChatMessage.objects.create(user=self.bob, role="user", content="Msg privada de Bob")

        with patch("ia.views.chamar_ia") as mock_ia:
            mock_ia.return_value = {"success": True, "response": "Resposta Assistente", "total_tokens": 30, "error": None}
            resp_chat = self.client_alice.post(
                "/ia/assistente/chat/", data=json.dumps({"message": "Pergunta nova"}), content_type="application/json"
            )
            self.assertEqual(resp_chat.status_code, 200)
            sent_prompt = mock_ia.call_args.kwargs["prompt"]
            # Janela das últimas 5 mensagens: Msg antiga 2..6 devem estar presentes; Msg antiga 0 e 1 NÃO devem estar
            self.assertNotIn("Msg antiga 0", sent_prompt)
            self.assertNotIn("Msg antiga 1", sent_prompt)
            self.assertIn("Msg antiga 6", sent_prompt)

        # Limpar histórico de Alice NÃO apaga histórico de Bob
        resp_clear = self.client_alice.post("/ia/assistente/clear/")
        self.assertEqual(resp_clear.status_code, 200)
        self.assertEqual(ChatMessage.objects.filter(user=self.alice).count(), 0)
        self.assertEqual(ChatMessage.objects.filter(user=self.bob).count(), 1)
