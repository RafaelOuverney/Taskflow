"""Executor de teste de carga multiusuário para o TaskFlow com geração automática de relatórios."""

from __future__ import annotations

import argparse
import random
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from requests.adapters import HTTPAdapter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from load_tests.metrics import RequestRecord, SLAConfig, summarize_results
from load_tests.report import write_reports
from load_tests.server import BenchmarkUserData, StandaloneTestServer

CSRF_INPUT_RE = re.compile(r'name=["\']csrfmiddlewaretoken["\']\s+value=["\']([^"\']+)["\']')


def _extract_csrf(session: requests.Session, html_text: str) -> str:
    cookie_token = session.cookies.get("csrftoken")
    if cookie_token:
        return cookie_token
    match = CSRF_INPUT_RE.search(html_text)
    return match.group(1) if match else ""


class VirtualUserWorker:
    """Simula o fluxo completo de um usuário concorrente autenticado no TaskFlow."""

    def __init__(
        self,
        vu_id: int,
        base_url: str,
        user_data: BenchmarkUserData | None,
        think_min: float,
        think_max: float,
        stop_event: threading.Event,
        records: list[RequestRecord],
        records_lock: threading.Lock,
        timeout_sec: float = 15.0,
    ) -> None:
        self.vu_id = vu_id
        self.base_url = base_url.rstrip("/")
        self.user_data = user_data
        self.think_min = think_min
        self.think_max = think_max
        self.stop_event = stop_event
        self.records = records
        self.records_lock = records_lock
        self.timeout_sec = timeout_sec

        self.session = requests.Session()
        adapter = HTTPAdapter(pool_connections=4, pool_maxsize=4)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        self._csrf_token = ""
        self._notebook_id: int | None = user_data.notebook_id if user_data else None
        self._task_ids: list[int] = list(user_data.task_ids) if user_data else []
        self._equipe_id: int | None = user_data.equipe_id if user_data else None
        self._rng = random.Random(1000 + vu_id)

    def _record(
        self,
        method: str,
        endpoint_label: str,
        status_code: int,
        latency_ms: float,
        bytes_received: int,
        success: bool,
        error: str = "",
    ) -> None:
        rec = RequestRecord(
            endpoint=endpoint_label,
            method=method,
            status_code=status_code,
            latency_ms=latency_ms,
            bytes_received=bytes_received,
            success=success,
            timestamp=time.perf_counter(),
            error=error,
        )
        with self.records_lock:
            self.records.append(rec)

    def _request(
        self,
        method: str,
        path: str,
        endpoint_label: str,
        *,
        json_payload: dict[str, Any] | None = None,
        expect_json_success: bool = False,
        expected_status: tuple[int, ...] = (200,),
    ) -> requests.Response | None:
        url = f"{self.base_url}{path}"
        headers: dict[str, str] = {}
        if method.upper() == "POST":
            token = self.session.cookies.get("csrftoken") or self._csrf_token
            headers["X-CSRFToken"] = token
            headers["Referer"] = f"{self.base_url}/"

        t0 = time.perf_counter()
        try:
            resp = self.session.request(
                method=method,
                url=url,
                json=json_payload,
                headers=headers,
                allow_redirects=False,
                timeout=self.timeout_sec,
            )
            latency_ms = (time.perf_counter() - t0) * 1000.0
            size = len(resp.content or b"")

            ok = resp.status_code in expected_status
            err_msg = ""

            if not ok:
                err_msg = f"HTTP {resp.status_code} em {method} {endpoint_label}"
            elif expect_json_success:
                try:
                    payload = resp.json()
                    if not payload.get("success", False):
                        ok = False
                        err_msg = str(payload.get("message") or "JSON success=false")
                except ValueError:
                    ok = False
                    err_msg = "Resposta JSON inválida"

            if resp.cookies.get("csrftoken"):
                self._csrf_token = resp.cookies.get("csrftoken", self._csrf_token)

            self._record(
                method=method,
                endpoint_label=endpoint_label,
                status_code=resp.status_code,
                latency_ms=latency_ms,
                bytes_received=size,
                success=ok,
                error=err_msg,
            )
            return resp
        except Exception as exc:
            latency_ms = (time.perf_counter() - t0) * 1000.0
            self._record(
                method=method,
                endpoint_label=endpoint_label,
                status_code=0,
                latency_ms=latency_ms,
                bytes_received=0,
                success=False,
                error=f"{type(exc).__name__}: {exc}",
            )
            return None

    def authenticate(self) -> bool:
        resp = self._request("GET", "/", "/")
        if resp is None or resp.status_code != 200:
            return False
        self._csrf_token = _extract_csrf(self.session, resp.text)

        if self.user_data is not None:
            login_resp = self._request(
                "POST",
                "/",
                "/",
                json_payload={
                    "email": self.user_data.email,
                    "password": self.user_data.password,
                    "rememberMe": True,
                },
                expect_json_success=True,
            )
            return login_resp is not None and login_resp.status_code == 200

        unique_email = f"loadtest_ext_{self.vu_id}_{int(time.time() * 1000)}@taskflow.local"
        reg_resp = self._request(
            "POST",
            "/cadastro/",
            "/cadastro/",
            json_payload={
                "fullName": f"Usuario Carga {self.vu_id}",
                "email": unique_email,
                "password": "LoadTest@Password123",
                "confirmPassword": "LoadTest@Password123",
                "terms": True,
            },
            expect_json_success=True,
        )
        if reg_resp is None or reg_resp.status_code != 200:
            return False

        nb_resp = self._request(
            "POST",
            "/api/notebook/create/",
            "/api/notebook/create/",
            json_payload={"title": f"Caderno VU {self.vu_id}"},
            expect_json_success=True,
        )
        if nb_resp and nb_resp.status_code == 200:
            self._notebook_id = nb_resp.json().get("notebook", {}).get("id")

        t_resp = self._request(
            "POST",
            "/api/task/create/",
            "/api/task/create/",
            json_payload={"title": f"Tarefa Inicial VU {self.vu_id}", "priority": "high"},
            expect_json_success=True,
        )
        if t_resp and t_resp.status_code == 200:
            tid = t_resp.json().get("task", {}).get("id")
            if tid:
                self._task_ids.append(tid)

        return True

    def _build_weighted_actions(self) -> list[tuple[int, Any]]:
        actions: list[tuple[int, Any]] = [
            (20, lambda: self._request("GET", "/dashboard/", "/dashboard/")),
            (15, lambda: self._request("GET", "/tarefas/", "/tarefas/")),
            (
                10,
                lambda: self._request(
                    "GET",
                    "/tarefas/?priority=high&completed=false",
                    "/tarefas/?priority=high&completed=false",
                ),
            ),
            (
                15,
                lambda: self._request(
                    "GET",
                    "/api/task/list/",
                    "/api/task/list/",
                    expect_json_success=True,
                ),
            ),
            (5, self._action_create_task),
            (10, lambda: self._request("GET", "/caderno/", "/caderno/")),
            (8, lambda: self._request("GET", "/equipes/", "/equipes/")),
            (5, lambda: self._request("GET", "/ia/meu-consumo/", "/ia/meu-consumo/")),
        ]

        if self._task_ids:
            actions.append((10, self._action_toggle_task))
        if self._notebook_id is not None:
            actions.append((25, self._action_autosave_notebook))
        if self._equipe_id is not None:
            actions.append(
                (
                    5,
                    lambda: self._request(
                        "GET",
                        f"/equipes/{self._equipe_id}/",
                        "/equipes/<id>/",
                    ),
                )
            )
            actions.append(
                (
                    5,
                    lambda: self._request(
                        "GET",
                        f"/analise/?equipe={self._equipe_id}",
                        "/analise/?equipe=<id>",
                    ),
                )
            )
        return actions

    def _action_create_task(self) -> None:
        resp = self._request(
            "POST",
            "/api/task/create/",
            "/api/task/create/",
            json_payload={
                "title": f"Tarefa VU{self.vu_id} #{self._rng.randint(100, 9999)}",
                "priority": self._rng.choice(["low", "medium", "high"]),
            },
            expect_json_success=True,
        )
        if resp is not None and resp.status_code == 200:
            try:
                tid = resp.json().get("task", {}).get("id")
                if tid and len(self._task_ids) < 25:
                    self._task_ids.append(tid)
            except Exception:
                pass

    def _action_toggle_task(self) -> None:
        task_id = self._rng.choice(self._task_ids)
        self._request(
            "POST",
            "/api/task/toggle/",
            "/api/task/toggle/",
            json_payload={
                "task_id": task_id,
                "completed": self._rng.choice([True, False]),
            },
            expect_json_success=True,
        )

    def _action_autosave_notebook(self) -> None:
        self._request(
            "POST",
            "/api/notebook/save/",
            "/api/notebook/save/",
            json_payload={
                "notebook_id": self._notebook_id,
                "title": f"Caderno Benchmark {self.vu_id}",
                "content": (
                    f"<p>Sincronização automática VU {self.vu_id} "
                    f"iteração {self._rng.randint(1000, 9999)}</p>"
                ),
            },
            expect_json_success=True,
        )

    def run(self, initial_delay: float) -> None:
        if initial_delay > 0:
            if self.stop_event.wait(initial_delay):
                return

        if not self.authenticate():
            return

        actions = self._build_weighted_actions()
        weights = [w for w, _ in actions]
        callables = [fn for _, fn in actions]

        while not self.stop_event.is_set():
            action = self._rng.choices(callables, weights=weights, k=1)[0]
            action()
            if self.think_max > 0:
                pause = self._rng.uniform(self.think_min, self.think_max)
                if self.stop_event.wait(pause):
                    break


def run_load_test(args: argparse.Namespace) -> int:
    standalone_server: StandaloneTestServer | None = None
    users_data: list[BenchmarkUserData] = []
    target_url = args.url
    mode = "external"
    db_engine = "externo (servidor alvo)"
    debug_toolbar_enabled = False

    if not target_url:
        mode = "standalone"
        print(
            f"[TaskFlow LoadTest] Inicializando servidor isolado e populando {args.users} VUs..."
        )
        standalone_server = StandaloneTestServer(
            num_users=args.users,
            disable_debug_toolbar=args.no_debug_toolbar,
            sqlite_wal=args.sqlite_wal,
        )
        standalone_server.start()
        target_url = standalone_server.base_url
        users_data = standalone_server.users
        db_engine = standalone_server.database_engine
        debug_toolbar_enabled = standalone_server.debug_toolbar_enabled
        print(f"[TaskFlow LoadTest] Servidor ativo em {target_url} ({db_engine})")

    records: list[RequestRecord] = []
    records_lock = threading.Lock()
    stop_event = threading.Event()

    executed_at = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    timestamp_tag = datetime.now().strftime("%Y%m%d_%H%M%S")

    print(
        f"[TaskFlow LoadTest] Executando carga: {args.users} VUs | "
        f"Duração: {args.duration}s | Ramp-up: {args.ramp_up}s"
    )

    test_start = time.perf_counter()
    try:
        with ThreadPoolExecutor(max_workers=args.users) as pool:
            futures = []
            for idx in range(args.users):
                delay = (
                    (idx / max(1, args.users - 1)) * args.ramp_up
                    if args.users > 1 and args.ramp_up > 0
                    else 0.0
                )
                u_data = users_data[idx] if idx < len(users_data) else None
                worker = VirtualUserWorker(
                    vu_id=idx + 1,
                    base_url=target_url,
                    user_data=u_data,
                    think_min=args.think_min,
                    think_max=args.think_max,
                    stop_event=stop_event,
                    records=records,
                    records_lock=records_lock,
                )
                futures.append(pool.submit(worker.run, delay))

            time.sleep(args.duration)
            stop_event.set()

            for fut in futures:
                fut.result()
    finally:
        test_end = time.perf_counter()
        if standalone_server is not None:
            standalone_server.stop()

    metadata = {
        "executed_at": executed_at,
        "mode": mode,
        "target_url": target_url,
        "database_engine": db_engine,
        "debug_toolbar_enabled": debug_toolbar_enabled,
        "users": args.users,
        "duration_seconds": args.duration,
        "ramp_up_seconds": args.ramp_up,
        "think_time_range": f"{args.think_min}-{args.think_max}s",
    }

    sla = SLAConfig(
        max_error_rate_pct=args.max_error_rate,
        max_p95_ms=args.max_p95_ms,
        max_p99_ms=args.max_p99_ms,
    )

    summary = summarize_results(
        records=records,
        start_time=test_start,
        end_time=test_end,
        metadata=metadata,
        sla=sla,
    )

    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = PROJECT_ROOT / output_dir

    report_paths = write_reports(summary, output_dir, timestamp_tag)

    g = summary["global"]
    sla_status = "APROVADO" if summary["sla"]["passed"] else "REPROVADO"
    print("\n" + "=" * 68)
    print(f"RESULTADO DO TESTE DE CARGA — SLA: {sla_status}")
    print("=" * 68)
    print(
        f"Requisições: {g['total_requests']} | Falhas: {g['failures']} "
        f"({g['error_rate_pct']:.2f}%) | RPS: {g['rps']:.2f} req/s"
    )
    print(
        f"Latência (ms): média={g['avg_ms']:.2f} | p50={g['p50_ms']:.2f} | "
        f"p95={g['p95_ms']:.2f} | p99={g['p99_ms']:.2f} | máx={g['max_ms']:.2f}"
    )
    print("-" * 68)
    print(f"Relatório Markdown : {report_paths['markdown']}")
    print(f"Relatório HTML     : {report_paths['html']}")
    print(f"Relatório JSON     : {report_paths['json']}")
    print("=" * 68)

    if args.strict_sla and not summary["sla"]["passed"]:
        return 1
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Teste de carga concorrente do TaskFlow com geração automática de relatórios."
    )
    parser.add_argument("--users", type=int, default=20, help="Número de usuários virtuais (padrão: 20)")
    parser.add_argument("--duration", type=int, default=20, help="Duração em segundos (padrão: 20)")
    parser.add_argument("--ramp-up", type=float, default=3.0, help="Tempo de ramp-up em segundos (padrão: 3.0)")
    parser.add_argument("--think-min", type=float, default=0.1, help="Pausa mínima entre requisições (s)")
    parser.add_argument("--think-max", type=float, default=0.35, help="Pausa máxima entre requisições (s)")
    parser.add_argument(
        "--url",
        type=str,
        default="",
        help="URL de um servidor já ativo (ex: http://127.0.0.1:8000). Se omitido, sobe servidor isolado.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="load_tests/reports",
        help="Diretório de saída dos relatórios (padrão: load_tests/reports)",
    )
    parser.add_argument("--max-error-rate", type=float, default=2.0, help="SLA: taxa máxima de erro (%)")
    parser.add_argument("--max-p95-ms", type=float, default=1000.0, help="SLA: latência p95 máxima (ms)")
    parser.add_argument("--max-p99-ms", type=float, default=2000.0, help="SLA: latência p99 máxima (ms)")
    parser.add_argument(
        "--no-debug-toolbar",
        action="store_true",
        help="Desativa o Django Debug Toolbar no modo standalone para medir latência sem overhead de debug.",
    )
    parser.add_argument(
        "--sqlite-wal",
        action="store_true",
        help="Habilita journal_mode=WAL e timeout=20s no SQLite temporário do modo standalone.",
    )
    parser.add_argument(
        "--strict-sla",
        action="store_true",
        help="Retorna código de saída 1 caso algum critério de SLA falhe.",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(run_load_test(parse_args()))
