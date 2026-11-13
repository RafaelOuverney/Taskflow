"""Testes caixa-branca para models, forms, filters, mixins e templatetags do app pages."""

from django.contrib.auth.models import Group, User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase

from pages.filters import EquipeFilter, TaskFilter
from pages.forms import EquipeForm, ProfileUpdateForm, SecurityForm, UserUpdateForm
from pages.mixins import GroupRequiredMixin
from pages.models import Equipe, Notebook, SubTask, Task
from pages.templatetags.query_params import param_replace


class _DummyProtectedView(GroupRequiredMixin):
    group_required = ["Admins"]


class PagesModelsWhiteBoxTests(TestCase):
    """Verifica comportamento estrutural, ordenação e propriedades dos modelos de pages."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="modelos@taskflow.com",
            email="modelos@taskflow.com",
            password="Password@123",
        )

    def test_notebook_str_and_defaults(self) -> None:
        """Verifica valores padrão e representação textual de Notebook."""
        nb = Notebook.objects.create(owner=self.user)
        self.assertEqual(nb.title, "Novo Caderno")
        self.assertEqual(nb.visibility, "private")
        self.assertEqual(str(nb), "Novo Caderno")

    def test_task_subtask_properties_and_ordering(self) -> None:
        """Verifica propriedades subtasks_count/subtasks_completed e ordenação de SubTask."""
        task = Task.objects.create(title="Implementar API", owner=self.user, priority="high")
        s1 = SubTask.objects.create(title="Rota", task=task, completed=True)
        s2 = SubTask.objects.create(title="Testes", task=task, completed=False)

        self.assertEqual(str(task), "Implementar API")
        self.assertEqual(str(s1), "Rota")
        self.assertEqual(task.subtasks_count, 2)
        self.assertEqual(task.subtasks_completed, 1)
        # Ordenação Meta: ['completed', 'created_at'] -> pendentes (False) vêm antes de concluídas (True)
        self.assertEqual(list(task.subtasks.all()), [s2, s1])

    def test_equipe_str_and_m2m(self) -> None:
        """Verifica criação de Equipe, privacidade padrão e associação M2M."""
        member = User.objects.create_user(username="membro@taskflow.com", password="Password@123")
        eq = Equipe.objects.create(nome="Core QA", owner=self.user)
        eq.membros.add(self.user, member)

        self.assertEqual(str(eq), "Core QA")
        self.assertEqual(eq.privacidade, "private")
        self.assertEqual(eq.membros.count(), 2)


class PagesFormsAndFiltersWhiteBoxTests(TestCase):
    """Verifica validação de formulários, filtros django-filter, mixin RBAC e template tag."""

    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="filtros@taskflow.com",
            email="filtros@taskflow.com",
            password="Password@123",
            first_name="Ana",
        )
        self.other = User.objects.create_user(
            username="outro@taskflow.com",
            email="outro@taskflow.com",
            password="Password@123",
        )
        self.t_high_pending = Task.objects.create(
            title="Reunião Arquitetura", owner=self.user, priority="high", completed=False
        )
        self.t_low_done = Task.objects.create(
            title="Revisar Docs", owner=self.user, priority="low", completed=True
        )
        self.eq_pub = Equipe.objects.create(nome="Squad Alpha", privacidade="public", owner=self.user)
        self.eq_priv = Equipe.objects.create(nome="Squad Beta", privacidade="private", owner=self.user)

    def test_task_filter_branches(self) -> None:
        """Cobre todos os ramos de TaskFilter.filter_completed ('true', 'false', vazio) e busca."""
        qs = Task.objects.filter(owner=self.user)
        self.assertEqual(list(TaskFilter({"completed": "true"}, queryset=qs).qs), [self.t_low_done])
        self.assertEqual(list(TaskFilter({"completed": "false"}, queryset=qs).qs), [self.t_high_pending])
        self.assertEqual(TaskFilter({"completed": ""}, queryset=qs).qs.count(), 2)
        self.assertEqual(
            list(TaskFilter({"title": "reunião", "priority": "high"}, queryset=qs).qs),
            [self.t_high_pending],
        )

    def test_equipe_filter_branches(self) -> None:
        """Cobre filtragem por nome e privacidade em EquipeFilter."""
        qs = Equipe.objects.filter(owner=self.user)
        self.assertEqual(list(EquipeFilter({"nome": "alpha"}, queryset=qs).qs), [self.eq_pub])
        self.assertEqual(list(EquipeFilter({"privacidade": "private"}, queryset=qs).qs), [self.eq_priv])

    def test_forms_validation(self) -> None:
        """Valida caminhos válidos e inválidos de UserUpdateForm, ProfileUpdateForm, SecurityForm e EquipeForm."""
        u_form = UserUpdateForm(
            data={"first_name": "Ana", "last_name": "Silva", "email": "ana@taskflow.com"},
            instance=self.user,
        )
        self.assertTrue(u_form.is_valid())

        p_form = ProfileUpdateForm(data={"language": "pt-br", "phone_number": "11999990000"})
        self.assertTrue(p_form.is_valid())

        s_form_invalid = SecurityForm(data={"current_password": "123"})
        self.assertFalse(s_form_invalid.is_valid())

        eq_form = EquipeForm(
            data={
                "nome": "Time Teste",
                "descricao": "Escopo",
                "privacidade": "public",
                "membros": [self.user.id, self.other.id],
            }
        )
        self.assertTrue(eq_form.is_valid())

    def test_group_required_mixin_all_paths(self) -> None:
        """Testa os 3 ramos de GroupRequiredMixin: anônimo, usuário comum e membro de Admins."""
        from django.contrib.auth.models import AnonymousUser

        view = _DummyProtectedView()
        view.login_url = "index"

        # Ramo 1: usuário anônimo -> test_func False e redirect para login
        req_anon = self.factory.get("/analise/")
        req_anon.user = AnonymousUser()
        view.request = req_anon
        self.assertFalse(view.test_func())
        resp_anon = view.handle_no_permission()
        self.assertEqual(resp_anon.status_code, 302)

        # Ramo 2: usuário autenticado sem grupo Admins -> test_func False e redirect para dashboard
        req_user = self.factory.get("/analise/")
        req_user.user = self.user
        SessionMiddleware(lambda r: None).process_request(req_user)
        req_user.session.save()
        req_user._messages = FallbackStorage(req_user)
        view.request = req_user
        self.assertFalse(view.test_func())
        resp_user = view.handle_no_permission()
        self.assertEqual(resp_user.status_code, 302)
        self.assertEqual(resp_user.url, "/dashboard/")

        # Ramo 3: usuário no grupo Admins -> test_func True
        admins, _ = Group.objects.get_or_create(name="Admins")
        self.user.groups.add(admins)
        self.assertTrue(view.test_func())

    def test_param_replace_templatetag(self) -> None:
        """Testa substituição, adição, remoção e contexto sem request no param_replace."""
        self.assertEqual(param_replace({}), "")
        req = self.factory.get("/tarefas/?priority=high&page=1")
        result = param_replace({"request": req}, page=2, priority="")
        self.assertIn("page=2", result)
        self.assertNotIn("priority=", result)
