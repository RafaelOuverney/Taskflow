"""Testes caixa-branca para módulo de Equipes e Painel Analítico (AnaliseView)."""

from django.contrib.auth.models import Group, User
from django.db import connection
from django.test import Client, TestCase
from django.test.utils import CaptureQueriesContext

from pages.models import Equipe, Task


class PagesTeamsAndAnalyticsWhiteBoxTests(TestCase):
    """Cobre EquipeListView, EquipeDetailView, EquipeCreateView, EquipeUpdateView, EquipeDeleteView e AnaliseView."""

    def setUp(self) -> None:
        self.owner = User.objects.create_user(
            username="lider@taskflow.com", email="lider@taskflow.com", password="Password@123", first_name="Líder"
        )
        self.member = User.objects.create_user(
            username="membro@taskflow.com", email="membro@taskflow.com", password="Password@123", first_name="Membro"
        )
        self.outsider = User.objects.create_user(
            username="externo@taskflow.com", email="externo@taskflow.com", password="Password@123", first_name="Externo"
        )

        self.admins_group, _ = Group.objects.get_or_create(name="Admins")
        self.owner.groups.add(self.admins_group)

        self.equipe = Equipe.objects.create(nome="Squad Backend", privacidade="private", owner=self.owner)
        self.equipe.membros.add(self.owner, self.member)

        Task.objects.create(title="T1", owner=self.owner, priority="high", completed=True)
        Task.objects.create(title="T2", owner=self.member, priority="medium", completed=False)
        Task.objects.create(title="T3", owner=self.member, priority="low", completed=True)

        self.client_owner = Client()
        self.client_owner.force_login(self.owner)
        self.client_member = Client()
        self.client_member.force_login(self.member)
        self.client_outsider = Client()
        self.client_outsider.force_login(self.outsider)

    def test_equipe_list_visibility_and_query_optimization(self) -> None:
        """Verifica que EquipeListView mantém número constante de queries (sem N+1) ao crescer o número de equipes."""
        with CaptureQueriesContext(connection) as ctx_small:
            resp_small = self.client_member.get("/equipes/")
        self.assertEqual(resp_small.status_code, 200)

        for i in range(4):
            eq = Equipe.objects.create(nome=f"Extra {i}", owner=self.owner)
            eq.membros.add(self.owner, self.member)

        with CaptureQueriesContext(connection) as ctx_large:
            resp = self.client_member.get("/equipes/")
        self.assertEqual(resp.status_code, 200)
        # Paginado em 6 por página (5 equipes) e número de queries constante (sem N+1)
        self.assertEqual(len(resp.context["equipes"]), 5)
        self.assertEqual(len(ctx_large), len(ctx_small))

        resp_outsider = self.client_outsider.get("/equipes/")
        self.assertEqual(resp_outsider.status_code, 200)
        self.assertEqual(len(resp_outsider.context["equipes"]), 0)

    def test_equipe_detail_create_update_delete_permissions(self) -> None:
        """Verifica controle de acesso: membro lê detalhe, mas só owner edita/exclui."""
        self.assertEqual(self.client_member.get(f"/equipes/{self.equipe.id}/").status_code, 200)
        self.assertEqual(self.client_outsider.get(f"/equipes/{self.equipe.id}/").status_code, 404)

        # Membro não-owner não pode editar nem excluir (404 por get_queryset owner=user)
        self.assertEqual(self.client_member.get(f"/equipes/{self.equipe.id}/editar/").status_code, 404)
        self.assertEqual(self.client_member.post(f"/equipes/{self.equipe.id}/excluir/").status_code, 404)

        # Criação define owner corretamente
        resp_create = self.client_member.post(
            "/equipes/nova/",
            {"nome": "Squad Novo", "descricao": "Desc", "privacidade": "public", "membros": [self.member.id]},
        )
        self.assertEqual(resp_create.status_code, 302)
        created = Equipe.objects.get(nome="Squad Novo")
        self.assertEqual(created.owner, self.member)
        self.assertIn(self.member, created.membros.all())

        # Owner atualiza e exclui sua equipe
        resp_upd = self.client_owner.post(
            f"/equipes/{self.equipe.id}/editar/",
            {"nome": "Squad Backend v2", "descricao": "Atualizado", "privacidade": "public", "membros": [self.owner.id]},
        )
        self.assertEqual(resp_upd.status_code, 302)
        self.equipe.refresh_from_db()
        self.assertEqual(self.equipe.nome, "Squad Backend v2")

        resp_del = self.client_owner.post(f"/equipes/{self.equipe.id}/excluir/")
        self.assertEqual(resp_del.status_code, 302)
        self.assertFalse(Equipe.objects.filter(id=self.equipe.id).exists())

    def test_analise_view_rbac_and_metrics_calculation(self) -> None:
        """Verifica bloqueio RBAC para não-Admins e cálculo de métricas agregadas em AnaliseView."""
        # Usuário comum é redirecionado para /dashboard/
        resp_denied = self.client_member.get("/analise/")
        self.assertEqual(resp_denied.status_code, 302)
        self.assertEqual(resp_denied.url, "/dashboard/")

        # Admin com equipe liderada recebe métricas consolidadas e ordenadas por percentual desc
        resp_ok = self.client_owner.get(f"/analise/?equipe={self.equipe.id}")
        self.assertEqual(resp_ok.status_code, 200)
        self.assertEqual(resp_ok.context["total_tarefas"], 3)
        self.assertEqual(resp_ok.context["concluidas"], 2)
        self.assertEqual(resp_ok.context["pendentes"], 1)
        self.assertEqual(resp_ok.context["taxa_conclusao"], 67)
        self.assertEqual(resp_ok.context["prioridades"], {"high": 1, "medium": 1, "low": 1})
        membros_stats = resp_ok.context["analise_membros"]
        self.assertEqual(len(membros_stats), 2)
        self.assertEqual(membros_stats[0]["percentual"], 100)  # Líder (1/1)
        self.assertEqual(membros_stats[1]["percentual"], 50)   # Membro (1/2)

        # Admin sem equipes lideradas entra no ramo else (total_tarefas = 0)
        self.outsider.groups.add(self.admins_group)
        resp_empty = self.client_outsider.get("/analise/")
        self.assertEqual(resp_empty.status_code, 200)
        self.assertIsNone(resp_empty.context["equipe_selecionada"])
        self.assertEqual(resp_empty.context["total_tarefas"], 0)
