"""Coleta, agregação estatística e avaliação de SLA para testes de carga."""

from __future__ import annotations

import math
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class RequestRecord:
    """Registro individual de uma requisição HTTP executada no teste de carga."""

    endpoint: str
    method: str
    status_code: int
    latency_ms: float
    bytes_received: int
    success: bool
    timestamp: float
    error: str = ""


@dataclass(slots=True)
class SLAConfig:
    """Critérios de aceitação (SLA) avaliados ao final do teste."""

    max_error_rate_pct: float = 2.0
    max_p95_ms: float = 800.0
    max_p99_ms: float = 1500.0


def percentile(sorted_values: list[float], pct: float) -> float:
    """Calcula percentil usando interpolação linear sobre lista previamente ordenada."""
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    k = (len(sorted_values) - 1) * (pct / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_values[int(k)]
    return sorted_values[f] * (c - k) + sorted_values[c] * (k - f)


def _compute_latency_stats(latencies: list[float]) -> dict[str, float]:
    if not latencies:
        return {
            "min_ms": 0.0,
            "avg_ms": 0.0,
            "p50_ms": 0.0,
            "p90_ms": 0.0,
            "p95_ms": 0.0,
            "p99_ms": 0.0,
            "max_ms": 0.0,
            "stddev_ms": 0.0,
        }
    ordered = sorted(latencies)
    return {
        "min_ms": round(ordered[0], 2),
        "avg_ms": round(statistics.fmean(ordered), 2),
        "p50_ms": round(percentile(ordered, 50), 2),
        "p90_ms": round(percentile(ordered, 90), 2),
        "p95_ms": round(percentile(ordered, 95), 2),
        "p99_ms": round(percentile(ordered, 99), 2),
        "max_ms": round(ordered[-1], 2),
        "stddev_ms": round(statistics.pstdev(ordered), 2) if len(ordered) > 1 else 0.0,
    }


def _build_time_series(
    records: list[RequestRecord],
    start_time: float,
    duration_seconds: float,
    bucket_seconds: float = 2.0,
) -> list[dict[str, Any]]:
    if not records or duration_seconds <= 0:
        return []

    num_buckets = max(1, math.floor(duration_seconds / bucket_seconds))
    if duration_seconds - (num_buckets * bucket_seconds) >= bucket_seconds * 0.5:
        num_buckets += 1

    buckets: dict[int, list[RequestRecord]] = defaultdict(list)
    for rec in records:
        offset = max(0.0, rec.timestamp - start_time)
        idx = min(num_buckets - 1, int(offset // bucket_seconds))
        buckets[idx].append(rec)

    series: list[dict[str, Any]] = []
    for idx in range(num_buckets):
        items = buckets.get(idx, [])
        t_start = idx * bucket_seconds
        t_end = duration_seconds if idx == num_buckets - 1 else (idx + 1) * bucket_seconds
        actual_span = max(0.1, t_end - t_start)
        latencies = [r.latency_ms for r in items]
        failures = sum(1 for r in items if not r.success)
        stats = _compute_latency_stats(latencies)
        end_label = f"{t_end:.1f}" if abs(t_end - round(t_end)) >= 0.05 else f"{t_end:.0f}"
        series.append(
            {
                "bucket": idx + 1,
                "label": f"{t_start:.0f}-{end_label}s",
                "requests": len(items),
                "failures": failures,
                "rps": round(len(items) / actual_span, 2),
                "avg_ms": stats["avg_ms"],
                "p95_ms": stats["p95_ms"],
            }
        )
    return series


def _generate_diagnostics(
    global_stats: dict[str, Any],
    endpoints: list[dict[str, Any]],
    error_messages: Counter[str],
    metadata: dict[str, Any],
) -> list[str]:
    notes: list[str] = []

    if global_stats["error_rate_pct"] == 0.0:
        notes.append(
            "Nenhuma falha registrada durante todo o ciclo de carga; todas as respostas "
            "atenderam aos códigos HTTP e contratos JSON esperados."
        )
    else:
        notes.append(
            f"Taxa de erro global de {global_stats['error_rate_pct']:.2f}% "
            f"({global_stats['failures']} falhas em {global_stats['total_requests']} requisições)."
        )

    joined_errors = " ".join(error_messages.keys()).lower()
    if "locked" in joined_errors or "sqlite" in joined_errors:
        notes.append(
            "Contenção de escrita no SQLite detectada ('database is locked'). "
            "Para cargas concorrentes de escrita (como auto-save de cadernos), recomenda-se "
            "utilizar PostgreSQL via DATABASE_URL ou habilitar modo WAL no SQLite."
        )

    if endpoints:
        slowest = max(endpoints, key=lambda e: e["p95_ms"])
        notes.append(
            f"Endpoint com maior latência p95: `{slowest['method']} {slowest['endpoint']}` "
            f"(p95 = {slowest['p95_ms']:.2f} ms, média = {slowest['avg_ms']:.2f} ms)."
        )

        most_requested = max(endpoints, key=lambda e: e["requests"])
        notes.append(
            f"Endpoint mais demandado: `{most_requested['method']} {most_requested['endpoint']}` "
            f"com {most_requested['requests']} requisições ({most_requested['rps']:.2f} req/s)."
        )

    if metadata.get("debug_toolbar_enabled"):
        notes.append(
            "Django Debug Toolbar ativo durante o benchmark (DEBUG=True), adicionando overhead "
            "de instrumentação às respostas HTML. Em produção (DEBUG=False), a latência tende a ser menor."
        )

    return notes


def summarize_results(
    records: list[RequestRecord],
    start_time: float,
    end_time: float,
    metadata: dict[str, Any],
    sla: SLAConfig | None = None,
) -> dict[str, Any]:
    """Consolida todos os registros em métricas globais, por endpoint e avaliação de SLA."""
    sla = sla or SLAConfig()
    elapsed = max(0.001, end_time - start_time)

    total_requests = len(records)
    failures = sum(1 for r in records if not r.success)
    successes = total_requests - failures
    error_rate_pct = round((failures / total_requests) * 100.0, 2) if total_requests else 0.0
    total_bytes = sum(r.bytes_received for r in records)
    global_lat = _compute_latency_stats([r.latency_ms for r in records])

    global_stats: dict[str, Any] = {
        "total_requests": total_requests,
        "successes": successes,
        "failures": failures,
        "error_rate_pct": error_rate_pct,
        "duration_seconds": round(elapsed, 2),
        "rps": round(total_requests / elapsed, 2),
        "total_bytes": total_bytes,
        "total_kb": round(total_bytes / 1024.0, 2),
        "throughput_kbps": round((total_bytes / 1024.0) / elapsed, 2),
        **global_lat,
    }

    grouped: dict[tuple[str, str], list[RequestRecord]] = defaultdict(list)
    status_codes: Counter[str] = Counter()
    error_messages: Counter[str] = Counter()

    for rec in records:
        grouped[(rec.method, rec.endpoint)].append(rec)
        status_key = str(rec.status_code) if rec.status_code > 0 else "EXC"
        status_codes[status_key] += 1
        if not rec.success and rec.error:
            error_messages[rec.error] += 1

    endpoints: list[dict[str, Any]] = []
    for (method, endpoint), items in sorted(
        grouped.items(), key=lambda kv: len(kv[1]), reverse=True
    ):
        ep_failures = sum(1 for r in items if not r.success)
        ep_lat = _compute_latency_stats([r.latency_ms for r in items])
        endpoints.append(
            {
                "method": method,
                "endpoint": endpoint,
                "requests": len(items),
                "failures": ep_failures,
                "error_rate_pct": round((ep_failures / len(items)) * 100.0, 2),
                "rps": round(len(items) / elapsed, 2),
                "bytes_received": sum(r.bytes_received for r in items),
                **ep_lat,
            }
        )

    sla_checks = [
        {
            "criterion": f"Taxa de erro global <= {sla.max_error_rate_pct:.2f}%",
            "measured": f"{global_stats['error_rate_pct']:.2f}%",
            "passed": global_stats["error_rate_pct"] <= sla.max_error_rate_pct,
        },
        {
            "criterion": f"Latência p95 global <= {sla.max_p95_ms:.0f} ms",
            "measured": f"{global_stats['p95_ms']:.2f} ms",
            "passed": global_stats["p95_ms"] <= sla.max_p95_ms,
        },
        {
            "criterion": f"Latência p99 global <= {sla.max_p99_ms:.0f} ms",
            "measured": f"{global_stats['p99_ms']:.2f} ms",
            "passed": global_stats["p99_ms"] <= sla.max_p99_ms,
        },
    ]
    sla_passed = total_requests > 0 and all(item["passed"] for item in sla_checks)

    bucket_seconds = 2.0 if elapsed <= 60 else max(5.0, round(elapsed / 25.0))
    time_series = _build_time_series(records, start_time, elapsed, bucket_seconds=bucket_seconds)
    diagnostics = _generate_diagnostics(global_stats, endpoints, error_messages, metadata)

    return {
        "metadata": metadata,
        "global": global_stats,
        "endpoints": endpoints,
        "status_codes": dict(sorted(status_codes.items())),
        "top_errors": [
            {"message": msg, "count": cnt} for msg, cnt in error_messages.most_common(10)
        ],
        "time_series": time_series,
        "sla": {
            "passed": sla_passed,
            "checks": sla_checks,
        },
        "diagnostics": diagnostics,
    }
