"""Testes caixa-branca para configurações centrais, roteamento e entrypoints do pacote Taskflow."""

from django.conf import settings
from django.test import SimpleTestCase
from django.urls import resolve

from Taskflow import asgi, wsgi


class CoreTaskflowWhiteBoxTests(SimpleTestCase):
    """Verifica roteamento principal, settings de segurança/sessão e aplicações WSGI/ASGI."""

    def test_url_resolution_across_apps(self) -> None:
        """Confirma que todas as rotas principais resolvem para suas respectivas views."""
        expected = {
            "/": "index",
            "/dashboard/": "dashboard",
            "/tarefas/": "tarefas",
            "/caderno/": "notebook",
            "/equipes/": "equipes",
            "/analise/": "analise",
            "/calendario/": "calendario",
            "/ia/config/": "ia_config",
            "/ia/assistente/": "ia_assistente",
        }
        for path, view_name in expected.items():
            match = resolve(path)
            self.assertEqual(match.url_name, view_name)

    def test_security_and_session_configuration(self) -> None:
        """Verifica flags de segurança de sessão e prioridade do Argon2PasswordHasher."""
        self.assertTrue(settings.SESSION_COOKIE_HTTPONLY)
        self.assertEqual(settings.SESSION_COOKIE_SAMESITE, "Lax")
        self.assertEqual(settings.PASSWORD_HASHERS[0], "django.contrib.auth.hashers.Argon2PasswordHasher")
        self.assertIn("django.middleware.csrf.CsrfViewMiddleware", settings.MIDDLEWARE)

    def test_wsgi_and_asgi_entrypoints(self) -> None:
        """Garante que os objetos application WSGI e ASGI são chamáveis válidos."""
        self.assertTrue(callable(wsgi.application))
        self.assertTrue(callable(asgi.application))
