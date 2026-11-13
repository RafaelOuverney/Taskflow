"""Testes caixa-branca para autenticação, cadastro, logout, páginas públicas e perfil."""

import json

from django.contrib.auth.models import User
from django.test import Client, TestCase


class PagesAuthAndProfileWhiteBoxTests(TestCase):
    """Cobre os caminhos de controle de IndexView, CadastroView, LogoutView, PerfilView e AlterarSenhaView."""

    def setUp(self) -> None:
        self.client = Client()
        self.user = User.objects.create_user(
            username="alice@taskflow.com",
            email="alice@taskflow.com",
            password="Password@123",
            first_name="Alice",
        )

    def test_index_get_unauthenticated_and_authenticated_redirect(self) -> None:
        """GET / renderiza index para anônimo e redireciona para /dashboard/ quando autenticado."""
        resp_anon = self.client.get("/")
        self.assertEqual(resp_anon.status_code, 200)

        self.client.force_login(self.user)
        resp_auth = self.client.get("/")
        self.assertEqual(resp_auth.status_code, 302)
        self.assertEqual(resp_auth.url, "/dashboard/")

    def test_index_post_all_branches(self) -> None:
        """Cobre campos vazios (400), credenciais inválidas (401), rememberMe True/False (200) e JSON inválido (500)."""
        resp_empty = self.client.post("/", data=json.dumps({"email": "", "password": ""}), content_type="application/json")
        self.assertEqual(resp_empty.status_code, 400)

        resp_wrong = self.client.post(
            "/",
            data=json.dumps({"email": "alice@taskflow.com", "password": "WrongPassword"}),
            content_type="application/json",
        )
        self.assertEqual(resp_wrong.status_code, 401)

        resp_ok = self.client.post(
            "/",
            data=json.dumps({"email": "alice@taskflow.com", "password": "Password@123", "rememberMe": True}),
            content_type="application/json",
        )
        self.assertEqual(resp_ok.status_code, 200)
        self.assertTrue(resp_ok.json()["success"])
        self.assertTrue(self.client.session.get("remember_me"))

        self.client.logout()
        resp_no_remember = self.client.post(
            "/",
            data=json.dumps({"email": "alice@taskflow.com", "password": "Password@123", "rememberMe": False}),
            content_type="application/json",
        )
        self.assertEqual(resp_no_remember.status_code, 200)
        self.assertFalse(self.client.session.get("remember_me"))

        resp_bad_json = self.client.post("/", data="{bad", content_type="application/json")
        self.assertEqual(resp_bad_json.status_code, 500)

    def test_cadastro_all_validation_branches(self) -> None:
        """Cobre todos os desvios de CadastroView: GET, campos faltando, nome < 3, senhas, termos, duplicado e sucesso."""
        self.assertEqual(self.client.get("/cadastro/").status_code, 200)

        cases = [
            ({"fullName": "", "email": "a@b.com", "password": "Password@1", "confirmPassword": "Password@1", "terms": True}, 400),
            ({"fullName": "Lu", "email": "a@b.com", "password": "Password@1", "confirmPassword": "Password@1", "terms": True}, 400),
            ({"fullName": "Lucas", "email": "a@b.com", "password": "Password@1", "confirmPassword": "Diff", "terms": True}, 400),
            ({"fullName": "Lucas", "email": "a@b.com", "password": "Password@1", "confirmPassword": "Password@1", "terms": False}, 400),
            ({"fullName": "Alice", "email": "alice@taskflow.com", "password": "Password@1", "confirmPassword": "Password@1", "terms": True}, 400),
        ]
        for payload, expected_status in cases:
            resp = self.client.post("/cadastro/", data=json.dumps(payload), content_type="application/json")
            self.assertEqual(resp.status_code, expected_status)
            self.assertFalse(resp.json()["success"])

        resp_ok = self.client.post(
            "/cadastro/",
            data=json.dumps(
                {
                    "fullName": "Bruno Costa Silva",
                    "email": "bruno@taskflow.com",
                    "password": "Password@123",
                    "confirmPassword": "Password@123",
                    "terms": True,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(resp_ok.status_code, 200)
        self.assertTrue(resp_ok.json()["success"])
        created = User.objects.get(email="bruno@taskflow.com")
        self.assertEqual(created.first_name, "Bruno")
        self.assertEqual(created.last_name, "Costa Silva")

        # Usuário já autenticado redireciona ao acessar /cadastro/
        self.assertEqual(self.client.get("/cadastro/").status_code, 302)

    def test_public_pages_and_logout(self) -> None:
        """Verifica RecuperacaoView, SobreView e LogoutView."""
        self.assertEqual(self.client.get("/recuperacao/").status_code, 200)
        self.assertEqual(self.client.get("/sobre/").status_code, 200)

        self.client.force_login(self.user)
        resp_logout = self.client.get("/logout/")
        self.assertEqual(resp_logout.status_code, 302)
        self.assertEqual(resp_logout.url, "/")

    def test_perfil_and_alterar_senha_branches(self) -> None:
        """Cobre PerfilView e os caminhos de erro/sucesso em AlterarSenhaView."""
        self.client.force_login(self.user)
        self.assertEqual(self.client.get("/perfil/").status_code, 200)

        # Senha atual incorreta
        r1 = self.client.post(
            "/perfil/senha/",
            {"current_password": "Errada", "new_password": "NewPassword@1", "confirm_password": "NewPassword@1"},
        )
        self.assertEqual(r1.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("Password@123"))

        # Nova senha não coincide
        r2 = self.client.post(
            "/perfil/senha/",
            {"current_password": "Password@123", "new_password": "NewPassword@1", "confirm_password": "OtherPassword@1"},
        )
        self.assertEqual(r2.status_code, 302)

        # Nova senha < 8 caracteres
        r3 = self.client.post(
            "/perfil/senha/",
            {"current_password": "Password@123", "new_password": "Curta", "confirm_password": "Curta"},
        )
        self.assertEqual(r3.status_code, 302)

        # Formulário inválido (campo vazio)
        r4 = self.client.post("/perfil/senha/", {})
        self.assertEqual(r4.status_code, 302)

        # Sucesso
        r5 = self.client.post(
            "/perfil/senha/",
            {"current_password": "Password@123", "new_password": "NewPassword@123", "confirm_password": "NewPassword@123"},
        )
        self.assertEqual(r5.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPassword@123"))
