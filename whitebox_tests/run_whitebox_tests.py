"""Executor unificado de testes caixa-branca do TaskFlow com cobertura real e relatório único."""

from __future__ import annotations

import dis
import os
import sys
import time
import types
import unittest
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

TARGET_FILES: list[tuple[str, Path]] = [
    ("pages", PROJECT_ROOT / "pages" / "models.py"),
    ("pages", PROJECT_ROOT / "pages" / "views.py"),
    ("pages", PROJECT_ROOT / "pages" / "forms.py"),
    ("pages", PROJECT_ROOT / "pages" / "filters.py"),
    ("pages", PROJECT_ROOT / "pages" / "mixins.py"),
    ("pages", PROJECT_ROOT / "pages" / "urls.py"),
    ("pages", PROJECT_ROOT / "pages" / "templatetags" / "query_params.py"),
    ("ia", PROJECT_ROOT / "ia" / "models.py"),
    ("ia", PROJECT_ROOT / "ia" / "views.py"),
    ("ia", PROJECT_ROOT / "ia" / "forms.py"),
    ("ia", PROJECT_ROOT / "ia" / "services.py"),
    ("ia", PROJECT_ROOT / "ia" / "urls.py"),
    ("Taskflow", PROJECT_ROOT / "Taskflow" / "urls.py"),
    ("Taskflow", PROJECT_ROOT / "Taskflow" / "wsgi.py"),
    ("Taskflow", PROJECT_ROOT / "Taskflow" / "asgi.py"),
]

MODULE_LABELS = {
    "whitebox_tests.test_pages_models_forms_filters": "pages (models, forms, filters, mixins, templatetags)",
    "whitebox_tests.test_pages_auth_profile": "pages (autenticação, cadastro e perfil)",
    "whitebox_tests.test_pages_notebooks_tasks": "pages (dashboard, cadernos, tarefas, subtarefas, anti-IDOR)",
    "whitebox_tests.test_pages_teams_analytics": "pages (equipes, RBAC e painel analítico)",
    "whitebox_tests.test_ia_module": "ia (models, forms, services e views)",
    "whitebox_tests.test_core_taskflow": "Taskflow (urls, settings, wsgi, asgi)",
}


@dataclass(slots=True)
class TestCaseOutcome:
    module: str
    class_name: str
    method_name: str
    description: str
    status: str
    duration_ms: float
    detail: str = ""


class LineCoverageTracker:
    """Rastreia linhas executadas nos módulos-alvo via sys.settrace + dis.findlinestarts."""

    def __init__(self, target_paths: list[Path]) -> None:
        self.targets = {str(p.resolve()).lower(): p.resolve() for p in target_paths if p.exists()}
        self.executed: dict[str, set[int]] = defaultdict(set)
        self._file_cache: dict[str, str | None] = {}
        self._prev_trace: Any = None

    def _resolve_target_key(self, code_file: str) -> str | None:
        cached = self._file_cache.get(code_file, "__MISS__")
        if cached != "__MISS__":
            return cached  # type: ignore[return-value]
        if not code_file or not code_file.endswith(".py"):
            self._file_cache[code_file] = None
            return None
        key = str(Path(code_file).resolve()).lower()
        resolved = key if key in self.targets else None
        self._file_cache[code_file] = resolved
        return resolved

    def _tracer(self, frame: types.FrameType, event: str, arg: Any) -> Any:
        key = self._resolve_target_key(frame.f_code.co_filename)
        if key is None:
            return None
        if event == "line":
            self.executed[key].add(frame.f_lineno)
        return self._tracer

    def start(self) -> None:
        self._prev_trace = sys.gettrace()
        sys.settrace(self._tracer)

    def stop(self) -> None:
        sys.settrace(self._prev_trace)

    @staticmethod
    def _executable_lines(file_path: Path) -> set[int]:
        source = file_path.read_text(encoding="utf-8")
        code_obj = compile(source, str(file_path), "exec")
        lines: set[int] = set()

        def walk(co: types.CodeType) -> None:
            for _, lineno in dis.findlinestarts(co):
                if lineno is not None and lineno > 0:
                    lines.add(lineno)
            for const in co.co_consts:
                if isinstance(const, types.CodeType):
                    walk(const)

        walk(code_obj)
        return lines

    def build_report_rows(self, labeled_paths: list[tuple[str, Path]]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for app_name, path in labeled_paths:
            resolved = path.resolve()
            key = str(resolved).lower()
            executable = self._executable_lines(resolved)
            hit = self.executed.get(key, set()) & executable
            total = len(executable)
            covered = len(hit)
            pct = round((covered / total) * 100.0, 2) if total else 100.0
            rel_path = resolved.relative_to(PROJECT_ROOT).as_posix()
            rows.append(
                {
                    "app": app_name,
                    "file": rel_path,
                    "executable": total,
                    "covered": covered,
                    "missed": total - covered,
                    "coverage_pct": pct,
                }
            )
        return rows


class WhiteBoxTextResult(unittest.TextTestResult):
    """Coleta resultado detalhado e tempo de cada caso de teste."""

    def __init__(self, stream: Any, descriptions: bool, verbosity: int) -> None:
        super().__init__(stream, descriptions, verbosity)
        self.outcomes: list[TestCaseOutcome] = []
        self._start_times: dict[str, float] = {}

    def startTest(self, test: unittest.TestCase) -> None:
        self._start_times[test.id()] = time.perf_counter()
        super().startTest(test)

    def _record(self, test: unittest.TestCase, status: str, detail: str = "") -> None:
        elapsed_ms = (time.perf_counter() - self._start_times.get(test.id(), time.perf_counter())) * 1000.0
        self.outcomes.append(
            TestCaseOutcome(
                module=test.__class__.__module__,
                class_name=test.__class__.__name__,
                method_name=test._testMethodName,
                description=(test.shortDescription() or "").strip(),
                status=status,
                duration_ms=round(elapsed_ms, 2),
                detail=detail.strip(),
            )
        )

    def addSuccess(self, test: unittest.TestCase) -> None:
        super().addSuccess(test)
        self._record(test, "PASS")

    def addFailure(self, test: unittest.TestCase, err: Any) -> None:
        super().addFailure(test, err)
        self._record(test, "FAIL", self._exc_info_to_string(err, test))

    def addError(self, test: unittest.TestCase, err: Any) -> None:
        super().addError(test, err)
        self._record(test, "ERROR", self._exc_info_to_string(err, test))

    def addSkip(self, test: unittest.TestCase, reason: str) -> None:
        super().addSkip(test, reason)
        self._record(test, "SKIP", reason)


def render_unified_report(
    outcomes: list[TestCaseOutcome],
    coverage_rows: list[dict[str, Any]],
    total_duration_s: float,
    executed_at: str,
) -> str:
    total_tests = len(outcomes)
    passed = sum(1 for o in outcomes if o.status == "PASS")
    failed = sum(1 for o in outcomes if o.status == "FAIL")
    errors = sum(1 for o in outcomes if o.status == "ERROR")
    skipped = sum(1 for o in outcomes if o.status == "SKIP")
    pass_rate = round((passed / total_tests) * 100.0, 2) if total_tests else 0.0
    overall_status = "APROVADO" if (failed == 0 and errors == 0 and total_tests > 0) else "REPROVADO"

    total_exec = sum(r["executable"] for r in coverage_rows)
    total_cov = sum(r["covered"] for r in coverage_rows)
    total_cov_pct = round((total_cov / total_exec) * 100.0, 2) if total_exec else 0.0

    by_module: dict[str, list[TestCaseOutcome]] = defaultdict(list)
    for o in outcomes:
        by_module[o.module].append(o)

    lines: list[str] = [
        "# Relatório Unificado de Testes Caixa-Branca — TaskFlow",
        "",
        f"**Executado em:** {executed_at}  ",
        f"**Duração Total da Suíte:** {total_duration_s:.2f} s  ",
        f"**Status Geral:** **{overall_status}**",
        "",
        "---",
        "",
        "## 1. Sumário Executivo",
        "",
        "| Indicador | Valor |",
        "| :--- | ---: |",
        f"| Total de Casos de Teste | **{total_tests}** |",
        f"| Aprovados (`PASS`) | **{passed}** ({pass_rate:.2f}%) |",
        f"| Falhas (`FAIL`) | {failed} |",
        f"| Erros (`ERROR`) | {errors} |",
        f"| Ignorados (`SKIP`) | {skipped} |",
        f"| Cobertura Global de Linhas Executáveis | **{total_cov}/{total_exec} ({total_cov_pct:.2f}%)** |",
        "",
        "---",
        "",
        "## 2. Resultados Consolidados por Módulo de Teste",
        "",
        "| Módulo / Escopo | Total | Pass | Fail | Error | Duração (ms) | Status |",
        "| :--- | ---: | ---: | ---: | ---: | ---: | :---: |",
    ]

    for mod_name, items in by_module.items():
        label = MODULE_LABELS.get(mod_name, mod_name)
        m_pass = sum(1 for i in items if i.status == "PASS")
        m_fail = sum(1 for i in items if i.status == "FAIL")
        m_err = sum(1 for i in items if i.status == "ERROR")
        m_dur = sum(i.duration_ms for i in items)
        m_status = "Aprovado" if (m_fail == 0 and m_err == 0) else "Reprovado"
        lines.append(
            f"| {label} | {len(items)} | {m_pass} | {m_fail} | {m_err} | {m_dur:.2f} | **{m_status}** |"
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "## 3. Cobertura Estrutural de Código por Arquivo",
            "",
            "| App | Arquivo | Linhas Executáveis | Linhas Cobertas | Não Cobertas | Cobertura |",
            "| :--- | :--- | ---: | ---: | ---: | ---: |",
        ]
    )

    for r in coverage_rows:
        lines.append(
            f"| `{r['app']}` | `{r['file']}` | {r['executable']} | {r['covered']} | "
            f"{r['missed']} | **{r['coverage_pct']:.2f}%** |"
        )
    lines.append(
        f"| **Total** | **Todos os módulos principais** | **{total_exec}** | **{total_cov}** | "
        f"**{total_exec - total_cov}** | **{total_cov_pct:.2f}%** |"
    )

    lines.extend(
        [
            "",
            "---",
            "",
            "## 4. Matriz Completa dos Casos de Teste Caixa-Branca",
            "",
            "| # | Módulo | Classe / Método | Objetivo Estrutural | Tempo (ms) | Status |",
            "| ---: | :--- | :--- | :--- | ---: | :---: |",
        ]
    )

    for idx, o in enumerate(outcomes, start=1):
        mod_short = o.module.replace("whitebox_tests.", "")
        desc = o.description or o.method_name
        lines.append(
            f"| {idx} | `{mod_short}` | `{o.class_name}.{o.method_name}` | {desc} | {o.duration_ms:.2f} | **{o.status}** |"
        )

    failures_or_errors = [o for o in outcomes if o.status in ("FAIL", "ERROR")]
    if failures_or_errors:
        lines.extend(["", "---", "", "## 5. Detalhes de Falhas e Erros", ""])
        for o in failures_or_errors:
            lines.append(f"### `{o.class_name}.{o.method_name}` ({o.status})")
            lines.append("```text")
            lines.append(o.detail)
            lines.append("```")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    use_env_db = "--use-env-db" in sys.argv
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Taskflow.settings")

    tracker = LineCoverageTracker([path for _, path in TARGET_FILES])
    tracker.start()

    import django
    from django.conf import settings

    if not use_env_db:
        settings.DATABASES["default"] = {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }

    from django.test.runner import DiscoverRunner

    django.setup()

    class CapturingRunner(DiscoverRunner):
        def get_resultclass(self) -> type[unittest.TestResult]:
            return WhiteBoxTextResult

        def run_suite(self, suite: unittest.TestSuite, **kwargs: Any) -> unittest.TestResult:
            runner = self.test_runner(
                verbosity=self.verbosity,
                failfast=self.failfast,
                resultclass=self.get_resultclass(),
            )
            result = runner.run(suite)
            self.captured_result = result  # type: ignore[attr-defined]
            return result

    executed_at = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    t0 = time.perf_counter()

    runner = CapturingRunner(verbosity=2, interactive=False)
    failures = runner.run_tests(["whitebox_tests"])
    elapsed = time.perf_counter() - t0

    tracker.stop()

    result: WhiteBoxTextResult = runner.captured_result  # type: ignore[attr-defined]
    coverage_rows = tracker.build_report_rows(TARGET_FILES)
    report_md = render_unified_report(
        outcomes=result.outcomes,
        coverage_rows=coverage_rows,
        total_duration_s=elapsed,
        executed_at=executed_at,
    )

    report_path = PROJECT_ROOT / "whitebox_tests" / "reports" / "relatorio_caixa_branca.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_md, encoding="utf-8")

    print("\n" + "=" * 68)
    print(f"Relatório único de caixa-branca gerado em: {report_path}")
    print("=" * 68)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
