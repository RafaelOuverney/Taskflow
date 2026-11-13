"""Servidor WSGI isolado e seed de dados para execução standalone do teste de carga."""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(slots=True)
class BenchmarkUserData:
    """Credenciais e IDs pertencentes a cada usuário virtual."""

    username: str
    email: str
    password: str
    notebook_id: int
    task_ids: list[int]
    equipe_id: int


class QuietWSGIRequestHandler:
    """Mixin/fábrica criada dinamicamente após django.setup()."""


class StandaloneTestServer:
    """Sobe o TaskFlow com SQLite temporário e dados isolados para teste de carga."""

    def __init__(
        self,
        num_users: int,
        disable_debug_toolbar: bool = False,
        sqlite_wal: bool = False,
    ) -> None:
        self.num_users = num_users
        self.disable_debug_toolbar = disable_debug_toolbar
        self.sqlite_wal = sqlite_wal
        self._tmp_dir: Path | None = None
        self._httpd: Any = None
        self._thread: threading.Thread | None = None
        self.base_url: str = ""
        self.database_engine: str = ""
        self.debug_toolbar_enabled: bool = True
        self.users: list[BenchmarkUserData] = []

    def start(self) -> None:
        if str(PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(PROJECT_ROOT))

        self._tmp_dir = Path(tempfile.mkdtemp(prefix="taskflow_loadtest_"))
        temp_db = self._tmp_dir / "loadtest.sqlite3"

        os.environ["DJANGO_SETTINGS_MODULE"] = "Taskflow.settings"

        import django
        from django.conf import settings

        settings.DATABASES["default"] = {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": temp_db,
            "TIME_ZONE": settings.TIME_ZONE,
            "CONN_HEALTH_CHECKS": False,
            "CONN_MAX_AGE": 0,
            "AUTOCOMMIT": True,
            "ATOMIC_REQUESTS": False,
            "OPTIONS": {"timeout": 20} if self.sqlite_wal else {},
        }
        if self.disable_debug_toolbar:
            settings.INTERNAL_IPS = set()
            self.debug_toolbar_enabled = False
        else:
            self.debug_toolbar_enabled = bool(settings.DEBUG and settings.INTERNAL_IPS)

        django.setup()

        from django.contrib.staticfiles.handlers import StaticFilesHandler
        from django.core.management import call_command
        from django.core.servers.basehttp import ThreadedWSGIServer, WSGIRequestHandler
        from django.core.wsgi import get_wsgi_application
        from django.db import connection

        call_command("migrate", verbosity=0, interactive=False)

        if self.sqlite_wal:
            with connection.cursor() as cursor:
                cursor.execute("PRAGMA journal_mode=WAL;")
                cursor.execute("PRAGMA synchronous=NORMAL;")

        self.database_engine = f"sqlite3 (temporário{', WAL' if self.sqlite_wal else ''})"
        self.users = self._seed_benchmark_data(self.num_users)

        class SilentHandler(WSGIRequestHandler):
            def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
                return

        app = StaticFilesHandler(get_wsgi_application())
        self._httpd = ThreadedWSGIServer(("127.0.0.1", 0), SilentHandler)
        self._httpd.daemon_threads = True
        self._httpd.set_app(app)

        host, port = self._httpd.server_address
        self.base_url = f"http://{host}:{port}"

        self._thread = threading.Thread(
            target=self._httpd.serve_forever,
            name="taskflow-loadtest-wsgi",
            daemon=True,
        )
        self._thread.start()

    def _seed_benchmark_data(self, count: int) -> list[BenchmarkUserData]:
        from django.contrib.auth.models import Group, User
        from pages.models import Equipe, Notebook, SubTask, Task

        admins_group, _ = Group.objects.get_or_create(name="Admins")
        seeded: list[BenchmarkUserData] = []
        password = "LoadTest@Password123"

        for idx in range(1, count + 1):
            email = f"loadtest_vu_{idx}@taskflow.local"
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=f"Usuário{idx}",
                last_name="Carga",
            )
            user.groups.add(admins_group)

            notebook = Notebook.objects.create(
                title=f"Caderno Benchmark {idx}",
                owner=user,
                content="<p>Conteúdo inicial do caderno de teste de carga.</p>",
                visibility="private",
            )

            task_ids: list[int] = []
            for t_idx, prio in enumerate(["high", "medium", "low"], start=1):
                task = Task.objects.create(
                    title=f"Tarefa Carga {idx}-{t_idx}",
                    description="Gerada automaticamente para benchmark.",
                    owner=user,
                    priority=prio,
                    completed=(t_idx == 3),
                )
                SubTask.objects.create(
                    title=f"Subtarefa {t_idx}.1",
                    task=task,
                    completed=False,
                )
                task_ids.append(task.id)

            equipe = Equipe.objects.create(
                nome=f"Equipe Carga {idx}",
                descricao="Equipe criada para o teste de carga.",
                privacidade="private",
                owner=user,
            )
            equipe.membros.add(user)

            seeded.append(
                BenchmarkUserData(
                    username=email,
                    email=email,
                    password=password,
                    notebook_id=notebook.id,
                    task_ids=task_ids,
                    equipe_id=equipe.id,
                )
            )

        return seeded

    def stop(self) -> None:
        if self._httpd is not None:
            try:
                self._httpd.shutdown()
                self._httpd.server_close()
            except Exception:
                pass
            self._httpd = None

        try:
            from django.db import connections

            connections.close_all()
        except Exception:
            pass

        if self._tmp_dir and self._tmp_dir.exists():
            shutil.rmtree(self._tmp_dir, ignore_errors=True)
            self._tmp_dir = None
