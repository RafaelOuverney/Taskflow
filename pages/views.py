import json
from collections import defaultdict
from datetime import datetime, time, timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_protect
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from pages.filters import EquipeFilter, TaskFilter
from pages.forms import EquipeForm, ProfileUpdateForm, SecurityForm, UserUpdateForm
from pages.mixins import GroupRequiredMixin
from pages.models import Equipe, Notebook, Task


def _serialize_task(task):
    """Serializa uma tarefa e suas subtarefas aproveitando o prefetch em memória."""
    subtasks = [
        {"id": s.id, "title": s.title, "completed": s.completed}
        for s in task.subtasks.all()
    ]
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "priority": task.priority,
        "completed": task.completed,
        "due_date": task.due_date.strftime("%d/%m/%Y %H:%M") if task.due_date else None,
        "subtasks": subtasks,
        "subtasks_count": len(subtasks),
        "subtasks_completed": sum(1 for s in subtasks if s["completed"]),
    }


class IndexView(TemplateView):
    template_name = "index.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return render(request, "index.html")

    @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            email = data.get("email", "").strip()
            password = data.get("password", "")
            remember_me = data.get("rememberMe", False)

            if not email or not password:
                return JsonResponse(
                    {"success": False, "message": "Email e senha são obrigatórios."},
                    status=400,
                )

            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
            
                if remember_me:
                    request.session.set_expiry(1209600)
                    request.session["remember_me"] = True
                else:
                    request.session.set_expiry(0)
                    request.session["remember_me"] = False

                return JsonResponse(
                    {
                        "success": True,
                        "message": "Login realizado com sucesso! Redirecionando...",
                        "redirect": "/dashboard/",
                    }
                )
            else:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Credenciais inválidas. Tente novamente.",
                    },
                    status=401,
                )

        except Exception as e:
            return JsonResponse(
                {"success": False, "message": f"Erro ao processar login: {str(e)}"},
                status=500,
            )


class RecuperacaoView(TemplateView):
    template_name = "recuperacao.html"

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CadastroView(TemplateView):
    template_name = "cadastro.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return render(request, "cadastro.html")

    @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            full_name = data.get("fullName", "").strip()
            email = data.get("email", "").strip()
            password = data.get("password", "")
            confirm_password = data.get("confirmPassword", "")
            terms = data.get("terms", False)

            if not all([full_name, email, password, confirm_password]):
                return JsonResponse(
                    {"success": False, "message": "Todos os campos são obrigatórios."},
                    status=400,
                )

            if len(full_name) < 3:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "O nome completo deve conter pelo menos 3 caracteres.",
                    },
                    status=400,
                )

            if password != confirm_password:
                return JsonResponse(
                    {"success": False, "message": "As senhas não coincidem."},
                    status=400,
                )

            if not terms:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Você deve aceitar os termos e condições.",
                    },
                    status=400,
                )

            if (
                User.objects.filter(email=email).exists()
                or User.objects.filter(username=email).exists()
            ):
                return JsonResponse(
                    {"success": False, "message": "Este email já está registrado."},
                    status=400,
                )

            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=full_name.split()[0],
                last_name=" ".join(full_name.split()[1:])
                if len(full_name.split()) > 1
                else "",
            )

            login(request, user)
            

            return JsonResponse(
                {
                    "success": True,
                    "message": "Cadastro realizado com sucesso! Redirecionando...",
                    "redirect": "/dashboard/",
                }
            )

        except Exception as e:
            return JsonResponse(
                {"success": False, "message": f"Erro ao processar cadastro: {str(e)}"},
                status=500,
            )


class LogoutView(TemplateView):
    template_name = "index.html"

    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect("index")


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"
    login_url = "index"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        todas_tarefas = Task.objects.filter(owner=user)

        stats = todas_tarefas.aggregate(
            total=Count("id"),
            concluidas=Count("id", filter=Q(completed=True)),
        )
        total = stats["total"]
        concluidas = stats["concluidas"]
        pendentes = total - concluidas

        tarefas_recentes = todas_tarefas.prefetch_related("subtasks").order_by("-created_at")[:5]

        minhas_equipes = Equipe.objects.filter(membros=user).order_by("-updated_at")[:3]

        hoje = timezone.localdate()
        inicio_janela = hoje - timedelta(days=6)
        inicio_dt = timezone.make_aware(
            datetime.combine(inicio_janela - timedelta(days=1), time.min)
        )
        contagem_por_dia = defaultdict(int)
        for dt in todas_tarefas.filter(
            completed=True, updated_at__gte=inicio_dt
        ).values_list("updated_at", flat=True):
            contagem_por_dia[timezone.localtime(dt).date()] += 1

        dias_semana = ["SEG", "TER", "QUA", "QUI", "SEX", "SÁB", "DOM"]
        tarefas_por_dia = []

        max_value = 1
        dados_brutos = []

        for i in range(6, -1, -1):
            dia = hoje - timedelta(days=i)
            count = contagem_por_dia.get(dia, 0)
            dados_brutos.append(count)
            max_value = max(max_value, count)

        for i, count in enumerate(dados_brutos):
            dia_atual = hoje - timedelta(days=6 - i)
            nome_dia = dias_semana[dia_atual.weekday()]
            percentual = int((count / max_value) * 200) if max_value > 0 else 0
            altura_final = max(percentual, 5)
            tarefas_por_dia.append(
                {"nome": nome_dia, "count": count, "percentual": altura_final}
            )

        context.update(
            {
                "user_name": user.first_name or user.email,
                "total_tarefas": total,
                "tarefas_concluidas": concluidas,
                "tarefas_pendentes": pendentes,
                "tarefas_recentes": tarefas_recentes,
                "minhas_equipes": minhas_equipes,
                "tarefas_por_dia": tarefas_por_dia,
            }
        )
        return context


class NotebookListView(LoginRequiredMixin, ListView):
    model = Notebook
    template_name = "caderno.html"
    context_object_name = "notebooks"
    login_url = "index"

    def get_queryset(self):
        return Notebook.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        notebook_id = self.kwargs.get("notebook_id")

        if notebook_id:
            context["notebook"] = self.get_queryset().filter(id=notebook_id).first()
        else:
            context["notebook"] = self.get_queryset().first()

        return context


class NotebookCreateAPI(LoginRequiredMixin, CreateView):
    model = Notebook
    fields = ["title"]

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            request.POST = request.POST.copy()
            request.POST.update(data)
        except json.JSONDecodeError:
            pass
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.owner = self.request.user
        self.object = form.save()

        return JsonResponse(
            {
                "success": True,
                "message": "Caderno criado com sucesso!",
                "notebook": {
                    "id": self.object.id,
                    "title": self.object.title,
                    "content": self.object.content,
                },
            }
        )

    def form_invalid(self, form):
        return JsonResponse(
            {"success": False, "message": "Erro de validação do formulário."},
            status=400,
        )


class NotebookSaveAPI(LoginRequiredMixin, UpdateView):
    model = Notebook
    fields = ["title", "content"]

    def get_queryset(self):
        return Notebook.objects.filter(owner=self.request.user)

    def get_object(self, queryset=None):
        notebook_id = self.request.POST.get("notebook_id")
        return self.get_queryset().get(id=notebook_id)

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            request.POST = request.POST.copy()
            request.POST.update(data)
        except json.JSONDecodeError:
            pass
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save()
        return JsonResponse(
            {
                "success": True,
                "message": "Caderno salvo com sucesso!",
                "updated_at": self.object.updated_at.strftime("%d/%m/%Y %H:%M"),
            }
        )


class NotebookDeleteAPI(LoginRequiredMixin, TemplateView):
    @method_decorator(csrf_protect)
    def post(self, request):
        from .models import Notebook

        try:
            data = json.loads(request.body)
            notebook_id = data.get("notebook_id")

            notebook = Notebook.objects.get(id=notebook_id, owner=request.user)
            notebook.delete()

            return JsonResponse(
                {"success": True, "message": "Caderno deletado com sucesso!"}
            )
        except Notebook.DoesNotExist:
            return JsonResponse(
                {"success": False, "message": "Caderno não encontrado."}, status=404
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "message": f"Erro ao deletar caderno: {str(e)}"},
                status=500,
            )


class NotebookGetListAPI(LoginRequiredMixin, TemplateView):
    def get(self, request):
        from .models import Notebook

        try:
            notebooks = Notebook.objects.filter(owner=request.user).values(
                "id", "title", "updated_at"
            )

            return JsonResponse({"success": True, "notebooks": list(notebooks)})
        except Exception as e:
            return JsonResponse(
                {"success": False, "message": f"Erro ao buscar cadernos: {str(e)}"},
                status=500,
            )


class TasksListView(LoginRequiredMixin, ListView):
    model = Task
    context_object_name = "tasks"
    paginate_by = 5
    template_name = "tarefas.html"
    login_url = "index"

    def get_queryset(self):
        qs = Task.objects.filter(owner=self.request.user).prefetch_related("subtasks")
        self.filterset = TaskFilter(self.request.GET, queryset=qs)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stats = Task.objects.filter(owner=self.request.user).aggregate(
            total=Count("id"),
            completed=Count("id", filter=Q(completed=True)),
        )
        total = stats["total"]
        completed = stats["completed"]
        context["user_name"] = self.request.user.first_name or self.request.user.email
        context["filter"] = self.filterset
        context["filterset"] = self.filterset
        context["tasks_page_data"] = [_serialize_task(task) for task in context["tasks"]]
        context["tasks_stats"] = {
            "total": total,
            "completed": completed,
            "pending": total - completed,
        }
        return context


class TaskCreateAPI(LoginRequiredMixin, TemplateView):
    @method_decorator(csrf_protect)
    def post(self, request):
        from .models import Task

        try:
            data = json.loads(request.body)
            title = data.get("title", "Nova Tarefa").strip()
            priority = data.get("priority", "medium")

            task = Task.objects.create(
                title=title, owner=request.user, priority=priority
            )

            return JsonResponse(
                {
                    "success": True,
                    "message": "Tarefa criada com sucesso!",
                    "task": {
                        "id": task.id,
                        "title": task.title,
                        "description": task.description,
                        "priority": task.priority,
                        "completed": task.completed,
                        "subtasks_count": task.subtasks_count,
                        "subtasks_completed": task.subtasks_completed,
                    },
                }
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "message": f"Erro ao criar tarefa: {str(e)}"},
                status=500,
            )


class TaskUpdateAPI(LoginRequiredMixin, TemplateView):
    @method_decorator(csrf_protect)
    def post(self, request):
        from .models import Task

        try:
            data = json.loads(request.body)
            task_id = data.get("task_id")
            title = data.get("title", "").strip()
            description = data.get("description", "")
            priority = data.get("priority", "medium")

            task = Task.objects.get(id=task_id, owner=request.user)
            task.title = title
            task.description = description
            task.priority = priority
            task.save()

            return JsonResponse(
                {"success": True, "message": "Tarefa atualizada com sucesso!"}
            )
        except Task.DoesNotExist:
            return JsonResponse(
                {"success": False, "message": "Tarefa não encontrada."}, status=404
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "message": f"Erro ao atualizar tarefa: {str(e)}"},
                status=500,
            )


class TaskToggleAPI(LoginRequiredMixin, TemplateView):
    @method_decorator(csrf_protect)
    def post(self, request):
        from .models import Task

        try:
            data = json.loads(request.body)
            task_id = data.get("task_id")
            completed = data.get("completed", False)

            task = Task.objects.get(id=task_id, owner=request.user)
            task.completed = completed
            task.save()

            return JsonResponse(
                {
                    "success": True,
                    "message": "Tarefa atualizada com sucesso!",
                    "completed": task.completed,
                }
            )
        except Task.DoesNotExist:
            return JsonResponse(
                {"success": False, "message": "Tarefa não encontrada."}, status=404
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "message": f"Erro ao atualizar tarefa: {str(e)}"},
                status=500,
            )


class TaskDeleteAPI(LoginRequiredMixin, TemplateView):
    @method_decorator(csrf_protect)
    def post(self, request):
        from .models import Task

        try:
            data = json.loads(request.body)
            task_id = data.get("task_id")

            task = Task.objects.get(id=task_id, owner=request.user)
            task.delete()

            return JsonResponse(
                {"success": True, "message": "Tarefa deletada com sucesso!"}
            )
        except Task.DoesNotExist:
            return JsonResponse(
                {"success": False, "message": "Tarefa não encontrada."}, status=404
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "message": f"Erro ao deletar tarefa: {str(e)}"},
                status=500,
            )


class SubTaskCreateAPI(LoginRequiredMixin, TemplateView):
    @method_decorator(csrf_protect)
    def post(self, request):
        from .models import Task, SubTask

        try:
            data = json.loads(request.body)
            task_id = data.get("task_id")
            title = data.get("title", "Nova Sub-tarefa").strip()

            task = Task.objects.get(id=task_id, owner=request.user)
            subtask = SubTask.objects.create(title=title, task=task)

            return JsonResponse(
                {
                    "success": True,
                    "message": "Sub-tarefa criada com sucesso!",
                    "subtask": {
                        "id": subtask.id,
                        "title": subtask.title,
                        "completed": subtask.completed,
                    },
                }
            )
        except Task.DoesNotExist:
            return JsonResponse(
                {"success": False, "message": "Tarefa não encontrada."}, status=404
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "message": f"Erro ao criar sub-tarefa: {str(e)}"},
                status=500,
            )


class SubTaskToggleAPI(LoginRequiredMixin, TemplateView):
    @method_decorator(csrf_protect)
    def post(self, request):
        from .models import SubTask, Task

        try:
            data = json.loads(request.body)
            subtask_id = data.get("subtask_id")
            completed = data.get("completed", False)

            subtask = SubTask.objects.get(id=subtask_id)
            if subtask.task.owner != request.user:
                return JsonResponse(
                    {"success": False, "message": "Acesso negado."}, status=403
                )

            subtask.completed = completed
            subtask.save()

            return JsonResponse(
                {
                    "success": True,
                    "message": "Sub-tarefa atualizada com sucesso!",
                    "completed": subtask.completed,
                }
            )
        except SubTask.DoesNotExist:
            return JsonResponse(
                {"success": False, "message": "Sub-tarefa não encontrada."}, status=404
            )
        except Exception as e:
            return JsonResponse(
                {
                    "success": False,
                    "message": f"Erro ao atualizar sub-tarefa: {str(e)}",
                },
                status=500,
            )


class SubTaskDeleteAPI(LoginRequiredMixin, TemplateView):
    @method_decorator(csrf_protect)
    def post(self, request):
        from .models import SubTask

        try:
            data = json.loads(request.body)
            subtask_id = data.get("subtask_id")

            subtask = SubTask.objects.get(id=subtask_id)
            if subtask.task.owner != request.user:
                return JsonResponse(
                    {"success": False, "message": "Acesso negado."}, status=403
                )

            subtask.delete()

            return JsonResponse(
                {"success": True, "message": "Sub-tarefa deletada com sucesso!"}
            )
        except SubTask.DoesNotExist:
            return JsonResponse(
                {"success": False, "message": "Sub-tarefa não encontrada."}, status=404
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "message": f"Erro ao deletar sub-tarefa: {str(e)}"},
                status=500,
            )


class TasksGetListAPI(LoginRequiredMixin, TemplateView):
    def get(self, request):
        try:
            base_qs = Task.objects.filter(owner=request.user).prefetch_related("subtasks")
            stats_agg = Task.objects.filter(owner=request.user).aggregate(
                total=Count("id"),
                completed=Count("id", filter=Q(completed=True)),
            )

            qs = base_qs
            if any(k in request.GET for k in ("title", "priority", "completed")):
                qs = TaskFilter(request.GET, queryset=qs).qs

            if "page" in request.GET:
                page_obj = Paginator(qs, 5).get_page(request.GET.get("page"))
                target_tasks = page_obj.object_list
            else:
                target_tasks = qs

            tasks_data = [_serialize_task(task) for task in target_tasks]
            total = stats_agg["total"]
            completed = stats_agg["completed"]

            return JsonResponse({
                "success": True,
                "tasks": tasks_data,
                "stats": {
                    "total": total,
                    "completed": completed,
                    "pending": total - completed,
                },
            })
        except Exception as e:
            return JsonResponse(
                {"success": False, "message": f"Erro ao buscar tarefas: {str(e)}"},
                status=500,
            )


class CalendarView(LoginRequiredMixin, TemplateView):
    template_name = "calendario.html"
    login_url = "index"

    def get_context_data(self, **kwargs):
        from .models import Task

        context = super().get_context_data(**kwargs)
        context["user_name"] = self.request.user.first_name or self.request.user.email
        context["tasks"] = Task.objects.filter(owner=self.request.user)
        return context


class SobreView(TemplateView):
    template_name = "sobre.html"


class PerfilView(LoginRequiredMixin, View):
    template_name = "perfil.html"
    login_url = "index"

    def _build_context(self, request, user_form=None, profile_form=None):
        extras = request.session.get("profile_extras", {})
        return {
            "user_form": user_form or UserUpdateForm(instance=request.user),
            "profile_form": profile_form or ProfileUpdateForm(initial=extras),
            "password_form": SecurityForm(),
        }

    def get(self, request):
        return render(request, self.template_name, self._build_context(request))

    @method_decorator(csrf_protect)
    def post(self, request):
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            request.session["profile_extras"] = profile_form.cleaned_data
            messages.success(request, "Perfil atualizado com sucesso!")
            return redirect("perfil")

        messages.error(request, "Erro ao atualizar o perfil. Verifique os campos.")
        return render(
            request,
            self.template_name,
            self._build_context(request, user_form=user_form, profile_form=profile_form),
        )


class AlterarSenhaView(LoginRequiredMixin, View):
    def post(self, request):
        form = SecurityForm(request.POST)
        if form.is_valid():
            current_password = form.cleaned_data.get("current_password")
            new_password = form.cleaned_data.get("new_password")
            confirm_password = form.cleaned_data.get("confirm_password")

            if not request.user.check_password(current_password):
                messages.error(request, "A senha atual está incorreta.")
                return redirect("perfil")

            if new_password != confirm_password:
                messages.error(request, "A nova senha e a confirmação não coincidem.")
                return redirect("perfil")

            if len(new_password) < 8:
                messages.error(
                    request, "A nova senha deve ter pelo menos 8 caracteres."
                )
                return redirect("perfil")

            request.user.set_password(new_password)
            request.user.save()

            update_session_auth_hash(request, request.user)

            messages.success(request, "Sua senha foi alterada com sucesso!")
        else:
            messages.error(request, "Erro ao alterar a senha. Verifique os campos.")

        return redirect("perfil")


class EquipeListView(LoginRequiredMixin, ListView):
    model = Equipe
    template_name = "equipes/equipe-lista.html"
    context_object_name = "equipes"
    paginate_by = 6

    def get_queryset(self):
        qs = (
            Equipe.objects.filter(
                Q(owner=self.request.user) | Q(membros=self.request.user)
            )
            .select_related("owner")
            .prefetch_related("membros")
            .distinct()
        )
        self.filterset = EquipeFilter(self.request.GET, queryset=qs)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter"] = self.filterset
        context["filterset"] = self.filterset
        return context


class EquipeDetailView(LoginRequiredMixin, DetailView):
    model = Equipe
    template_name = "equipes/equipe-detalhe.html"
    context_object_name = "equipe"

    def get_queryset(self):
        return Equipe.objects.filter(
            Q(owner=self.request.user) | Q(membros=self.request.user)
        ).distinct()


class EquipeCreateView(LoginRequiredMixin, CreateView):
    model = Equipe
    form_class = EquipeForm
    template_name = "equipes/equipe-form.html"
    success_url = reverse_lazy("equipes")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        self.object = form.save()
        self.object.membros.add(self.request.user)
        messages.success(self.request, f"Equipe '{self.object.nome}' criada com sucesso!")
        return super().form_valid(form)


class EquipeUpdateView(LoginRequiredMixin, UpdateView):
    model = Equipe
    form_class = EquipeForm
    template_name = "equipes/equipe-form.html"
    success_url = reverse_lazy("equipes")

    def get_queryset(self):
        return Equipe.objects.filter(owner=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, f"Equipe '{form.instance.nome}' atualizada com sucesso!")
        return super().form_valid(form)


class EquipeDeleteView(LoginRequiredMixin, DeleteView):
    model = Equipe
    template_name = "equipes/equipe-confirm-delete.html"
    success_url = reverse_lazy("equipes")

    def get_queryset(self):
        return Equipe.objects.filter(owner=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Equipe excluída com sucesso!")
        return super().form_valid(form)


class AnaliseView(LoginRequiredMixin, GroupRequiredMixin, TemplateView):
    """
    Página de Análise: apresenta a análise do grupo quanto às tarefas.
    Restrita aos líderes (owners) das equipes.
    """
    group_required = ['Admins']
    template_name = "analise.html"
    login_url = "index"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        equipes_lideradas = Equipe.objects.filter(owner=user).prefetch_related("membros")

        equipe_id = self.request.GET.get("equipe")
        equipe_selecionada = (
            equipes_lideradas.filter(id=equipe_id).first() if equipe_id else None
        )
        equipe_selecionada = equipe_selecionada or equipes_lideradas.first()

        total_tarefas = 0
        concluidas = 0
        pendentes = 0
        prioridades = {"high": 0, "medium": 0, "low": 0}
        analise_membros = []

        if equipe_selecionada:
            membros = list(equipe_selecionada.membros.all())
            tarefas_resumo = list(
                Task.objects.filter(owner__in=membros).values_list(
                    "owner_id", "priority", "completed"
                )
            )

            stats_por_membro = defaultdict(lambda: {"total": 0, "concluidas": 0})
            for owner_id, priority, completed in tarefas_resumo:
                total_tarefas += 1
                if completed:
                    concluidas += 1
                if priority in prioridades:
                    prioridades[priority] += 1
                stats_por_membro[owner_id]["total"] += 1
                if completed:
                    stats_por_membro[owner_id]["concluidas"] += 1

            pendentes = total_tarefas - concluidas

            for membro in membros:
                m_stats = stats_por_membro[membro.id]
                m_total = m_stats["total"]
                m_concluidas = m_stats["concluidas"]
                analise_membros.append(
                    {
                        "nome": membro.first_name or membro.username,
                        "email": membro.email,
                        "total": m_total,
                        "concluidas": m_concluidas,
                        "pendentes": m_total - m_concluidas,
                        "percentual": round((m_concluidas / m_total) * 100)
                        if m_total
                        else 0,
                        "eh_lider": membro == equipe_selecionada.owner,
                    }
                )

            analise_membros.sort(key=lambda m: m["percentual"], reverse=True)

        context.update(
            {
                "minhas_equipes": equipes_lideradas,
                "equipe_selecionada": equipe_selecionada,
                "total_tarefas": total_tarefas,
                "concluidas": concluidas,
                "pendentes": pendentes,
                "taxa_conclusao": round((concluidas / total_tarefas) * 100)
                if total_tarefas
                else 0,
                "prioridades": prioridades,
                "analise_membros": analise_membros,
            }
        )
        return context
