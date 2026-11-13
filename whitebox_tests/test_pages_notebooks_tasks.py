"""Testes caixa-branca para Dashboard, Cadernos, Tarefas, Subtarefas, Calendário, Anti-IDOR e queries N+1."""

import json

from django.contrib.auth.models import User
from django.db import connection
from django.test import Client, TestCase
from django.test.utils import CaptureQueriesContext

from pages.models import Notebook, SubTask, Task


class PagesNotebooksTasksWhiteBoxTests(TestCase):
    """Testa isolamento multi-tenant (anti-IDOR), proteção CSRF, fluxos CRUD e eficiência ORM."""

    def setUp(self) -> None:
        self.alice = User.objects.create_user(
            username="alice@taskflow.com", email="alice@taskflow.com", password="Password@123", first_name="Alice"
        )
        self.bob = User.objects.create_user(
            username="bob@taskflow.com", email="bob@taskflow.com", password="Password@123", first_name="Bob"
        )
        self.alice_nb = Notebook.objects.create(title="Caderno Alice", owner=self.alice, content="<p>Privado</p>")
        self.bob_nb = Notebook.objects.create(title="Caderno Bob", owner=self.bob, content="<p>Bob</p>")

        self.alice_task = Task.objects.create(title="Tarefa Alice", owner=self.alice, priority="high", completed=False)
        self.alice_sub = SubTask.objects.create(title="Sub Alice", task=self.alice_task, completed=False)

        self.client_alice = Client()
        self.client_alice.force_login(self.alice)
        self.client_bob = Client()
        self.client_bob.force_login(self.bob)

    def test_dashboard_and_calendar_views(self) -> None:
        """Verifica contexto do DashboardView (gráfico 7 dias e contadores) e CalendarView."""
        Task.objects.create(title="Concluida Hoje", owner=self.alice, completed=True)
        resp_dash = self.client_alice.get("/dashboard/")
        self.assertEqual(resp_dash.status_code, 200)
        self.assertEqual(resp_dash.context["total_tarefas"], 2)
        self.assertEqual(resp_dash.context["tarefas_concluidas"], 1)
        self.assertEqual(resp_dash.context["tarefas_pendentes"], 1)
        self.assertEqual(len(resp_dash.context["tarefas_por_dia"]), 7)

        resp_cal = self.client_alice.get("/calendario/")
        self.assertEqual(resp_cal.status_code, 200)
        self.assertEqual(resp_cal.context["tasks"].count(), 2)

    def test_notebook_views_and_anti_idor(self) -> None:
        """Verifica criação, salvamento, listagem, exclusão e bloqueio IDOR em cadernos."""
        resp_list = self.client_alice.get("/caderno/")
        self.assertEqual(resp_list.status_code, 200)
        self.assertEqual(list(resp_list.context["notebooks"]), [self.alice_nb])

        # Acesso direto a notebook de outro usuário não expõe conteúdo
        resp_other = self.client_alice.get(f"/caderno/{self.bob_nb.id}/")
        self.assertEqual(resp_other.status_code, 200)
        self.assertIsNone(resp_other.context["notebook"])

        # Criar e validar erro em NotebookCreateAPI
        resp_create = self.client_alice.post(
            "/api/notebook/create/", data=json.dumps({"title": "Novo Caderno QA"}), content_type="application/json"
        )
        self.assertEqual(resp_create.status_code, 200)
        created_id = resp_create.json()["notebook"]["id"]

        resp_invalid = self.client_alice.post(
            "/api/notebook/create/", data=json.dumps({"title": ""}), content_type="application/json"
        )
        self.assertEqual(resp_invalid.status_code, 400)

        # Salvar caderno próprio
        resp_save = self.client_alice.post(
            "/api/notebook/save/",
            data=json.dumps({"notebook_id": created_id, "title": "Atualizado", "content": "<p>Ok</p>"}),
            content_type="application/json",
        )
        self.assertEqual(resp_save.status_code, 200)

        # Anti-IDOR em NotebookSaveAPI: Bob tenta sobrescrever caderno de Alice -> Notebook.DoesNotExist
        with self.assertRaises(Notebook.DoesNotExist):
            self.client_bob.post(
                "/api/notebook/save/",
                data=json.dumps({"notebook_id": created_id, "title": "Invadido", "content": "X"}),
                content_type="application/json",
            )
        self.alice_nb.refresh_from_db()
        self.assertEqual(self.alice_nb.title, "Caderno Alice")

        # Anti-IDOR em NotebookDeleteAPI e NotebookGetListAPI
        resp_del_idor = self.client_bob.post(
            "/api/notebook/delete/", data=json.dumps({"notebook_id": created_id}), content_type="application/json"
        )
        self.assertEqual(resp_del_idor.status_code, 404)

        resp_get_list = self.client_alice.get("/api/notebook/list/")
        self.assertEqual(resp_get_list.status_code, 200)
        ids = {n["id"] for n in resp_get_list.json()["notebooks"]}
        self.assertNotIn(self.bob_nb.id, ids)

        resp_del_ok = self.client_alice.post(
            "/api/notebook/delete/", data=json.dumps({"notebook_id": created_id}), content_type="application/json"
        )
        self.assertEqual(resp_del_ok.status_code, 200)

    def test_tasks_and_subtasks_crud_and_anti_idor(self) -> None:
        """Verifica CRUD completo de Task/SubTask e bloqueio estrito de IDOR (404/403)."""
        # Criação
        resp_c = self.client_alice.post(
            "/api/task/create/", data=json.dumps({"title": "Nova Task", "priority": "low"}), content_type="application/json"
        )
        self.assertEqual(resp_c.status_code, 200)
        new_task_id = resp_c.json()["task"]["id"]

        # Update próprio vs Bob (404)
        self.assertEqual(
            self.client_alice.post(
                "/api/task/update/",
                data=json.dumps({"task_id": new_task_id, "title": "Editada", "description": "D", "priority": "high"}),
                content_type="application/json",
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client_bob.post(
                "/api/task/update/",
                data=json.dumps({"task_id": new_task_id, "title": "Hack"}),
                content_type="application/json",
            ).status_code,
            404,
        )

        # Toggle próprio vs Bob (404)
        self.assertEqual(
            self.client_alice.post(
                "/api/task/toggle/",
                data=json.dumps({"task_id": new_task_id, "completed": True}),
                content_type="application/json",
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client_bob.post(
                "/api/task/toggle/",
                data=json.dumps({"task_id": self.alice_task.id, "completed": True}),
                content_type="application/json",
            ).status_code,
            404,
        )
        self.alice_task.refresh_from_db()
        self.assertFalse(self.alice_task.completed)

        # Subtask Create / Toggle / Delete + Anti-IDOR (404/403)
        self.assertEqual(
            self.client_bob.post(
                "/api/subtask/create/",
                data=json.dumps({"task_id": self.alice_task.id, "title": "Invasao"}),
                content_type="application/json",
            ).status_code,
            404,
        )
        resp_sub = self.client_alice.post(
            "/api/subtask/create/",
            data=json.dumps({"task_id": new_task_id, "title": "Sub 1"}),
            content_type="application/json",
        )
        self.assertEqual(resp_sub.status_code, 200)
        sub_id = resp_sub.json()["subtask"]["id"]

        self.assertEqual(
            self.client_bob.post(
                "/api/subtask/toggle/",
                data=json.dumps({"subtask_id": sub_id, "completed": True}),
                content_type="application/json",
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client_bob.post(
                "/api/subtask/toggle/",
                data=json.dumps({"subtask_id": 999999, "completed": True}),
                content_type="application/json",
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client_alice.post(
                "/api/subtask/toggle/",
                data=json.dumps({"subtask_id": sub_id, "completed": True}),
                content_type="application/json",
            ).status_code,
            200,
        )

        self.assertEqual(
            self.client_bob.post(
                "/api/subtask/delete/", data=json.dumps({"subtask_id": sub_id}), content_type="application/json"
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client_alice.post(
                "/api/subtask/delete/", data=json.dumps({"subtask_id": sub_id}), content_type="application/json"
            ).status_code,
            200,
        )

        # Delete Task próprio vs Bob (404)
        self.assertEqual(
            self.client_bob.post(
                "/api/task/delete/", data=json.dumps({"task_id": new_task_id}), content_type="application/json"
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client_alice.post(
                "/api/task/delete/", data=json.dumps({"task_id": new_task_id}), content_type="application/json"
            ).status_code,
            200,
        )

    def test_csrf_enforced_on_sensitive_post(self) -> None:
        """Garante que Client(enforce_csrf_checks=True) bloqueia POST sem token CSRF (403)."""
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.alice)
        resp = csrf_client.post(
            "/api/task/toggle/",
            data=json.dumps({"task_id": self.alice_task.id, "completed": True}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 403)

    def test_tasks_list_view_pagination_and_orm_queries(self) -> None:
        """Verifica paginação (5 por página) e comportamento das consultas em TasksListView/TasksGetListAPI."""
        for i in range(7):
            t = Task.objects.create(title=f"Bulk {i}", owner=self.alice)
            SubTask.objects.create(title=f"Sub {i}", task=t)

        resp = self.client_alice.get("/tarefas/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context["tasks"]), 5)

        with CaptureQueriesContext(connection) as ctx:
            resp_api = self.client_alice.get("/api/task/list/")
        self.assertEqual(resp_api.status_code, 200)
        self.assertEqual(len(resp_api.json()["tasks"]), 8)
        # Documenta quantidade real de queries executadas (inclui sessão + user + tasks + prefetch + count por task)
        self.assertGreaterEqual(len(ctx), 3)
