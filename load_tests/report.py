"""Geradores de relatório (Markdown, HTML com gráficos SVG e JSON) para testes de carga."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


def render_markdown_report(summary: dict[str, Any]) -> str:
    """Renderiza relatório estruturado em Markdown."""
    meta = summary["metadata"]
    g = summary["global"]
    sla = summary["sla"]
    status_badge = "APROVADO" if sla["passed"] else "REPROVADO"

    lines: list[str] = [
        "# Relatório de Teste de Carga — TaskFlow",
        "",
        f"**Executado em:** {meta['executed_at']}  ",
        f"**Modo de Execução:** {meta['mode']}  ",
        f"**URL Alvo:** `{meta['target_url']}`  ",
        f"**Banco de Dados:** `{meta['database_engine']}`  ",
        f"**Usuários Virtuais (VUs):** {meta['users']} | "
        f"**Duração:** {meta['duration_seconds']}s | "
        f"**Ramp-up:** {meta['ramp_up_seconds']}s  ",
        f"**Status Geral (SLA):** **{status_badge}**",
        "",
        "---",
        "",
        "## 1. Sumário Executivo (Métricas Globais)",
        "",
        "| Métrica | Valor Medido |",
        "| :--- | ---: |",
        f"| Total de Requisições | **{g['total_requests']}** |",
        f"| Requisições com Sucesso | {g['successes']} |",
        f"| Falhas | {g['failures']} ({g['error_rate_pct']:.2f}%) |",
        f"| Duração Efetiva | {g['duration_seconds']:.2f} s |",
        f"| Vazão Média (RPS) | **{g['rps']:.2f} req/s** |",
        f"| Latência Mínima | {g['min_ms']:.2f} ms |",
        f"| Latência Média | {g['avg_ms']:.2f} ms |",
        f"| Mediana (p50) | {g['p50_ms']:.2f} ms |",
        f"| Percentil p90 | {g['p90_ms']:.2f} ms |",
        f"| Percentil p95 | **{g['p95_ms']:.2f} ms** |",
        f"| Percentil p99 | **{g['p99_ms']:.2f} ms** |",
        f"| Latência Máxima | {g['max_ms']:.2f} ms |",
        f"| Desvio Padrão | {g['stddev_ms']:.2f} ms |",
        f"| Tráfego Recebido | {g['total_kb']:.2f} KB ({g['throughput_kbps']:.2f} KB/s) |",
        "",
        "### Avaliação de Critérios de SLA",
        "",
        "| Critério | Valor Medido | Resultado |",
        "| :--- | ---: | :---: |",
    ]

    for check in sla["checks"]:
        res = "Aprovado" if check["passed"] else "Reprovado"
        lines.append(f"| {check['criterion']} | {check['measured']} | **{res}** |")

    lines.extend(
        [
            "",
            "---",
            "",
            "## 2. Desempenho Detalhado por Endpoint",
            "",
            "| Método | Endpoint | Req. | Falhas | Erro % | RPS | Mín (ms) | Média (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Máx (ms) |",
            "| :---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )

    for ep in summary["endpoints"]:
        lines.append(
            f"| `{ep['method']}` | `{ep['endpoint']}` | {ep['requests']} | {ep['failures']} | "
            f"{ep['error_rate_pct']:.2f}% | {ep['rps']:.2f} | {ep['min_ms']:.2f} | "
            f"{ep['avg_ms']:.2f} | {ep['p50_ms']:.2f} | {ep['p95_ms']:.2f} | "
            f"{ep['p99_ms']:.2f} | {ep['max_ms']:.2f} |"
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "## 3. Distribuição de Códigos de Status HTTP",
            "",
            "| Código HTTP | Quantidade | Participação |",
            "| :---: | ---: | ---: |",
        ]
    )

    total_req = max(1, g["total_requests"])
    for code, count in summary["status_codes"].items():
        pct = (count / total_req) * 100.0
        lines.append(f"| `{code}` | {count} | {pct:.2f}% |")

    if summary["top_errors"]:
        lines.extend(
            [
                "",
                "### Principais Erros Registrados",
                "",
                "| Mensagem / Causa | Ocorrências |",
                "| :--- | ---: |",
            ]
        )
        for err in summary["top_errors"]:
            msg = err["message"].replace("|", "\\|").replace("\n", " ")
            lines.append(f"| `{msg}` | {err['count']} |")

    if summary["time_series"]:
        lines.extend(
            [
                "",
                "---",
                "",
                "## 4. Evolução Temporal da Carga",
                "",
                "| Janela | Requisições | Falhas | RPS | Latência Média (ms) | p95 (ms) |",
                "| :---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for pt in summary["time_series"]:
            lines.append(
                f"| {pt['label']} | {pt['requests']} | {pt['failures']} | "
                f"{pt['rps']:.2f} | {pt['avg_ms']:.2f} | {pt['p95_ms']:.2f} |"
            )

    lines.extend(
        [
            "",
            "---",
            "",
            "## 5. Diagnóstico Automático e Recomendações",
            "",
        ]
    )
    for note in summary["diagnostics"]:
        lines.append(f"- {note}")

    lines.append("")
    return "\n".join(lines)


def _build_endpoint_bar_svg(endpoints: list[dict[str, Any]]) -> str:
    if not endpoints:
        return "<p>Sem dados de endpoints.</p>"

    top = endpoints[:12]
    max_p95 = max((ep["p95_ms"] for ep in top), default=1.0) or 1.0
    row_h = 34
    label_w = 260
    bar_max_w = 420
    width = label_w + bar_max_w + 130
    height = len(top) * row_h + 36

    svg_parts = [
        f'<svg viewBox="0 0 {width} {height}" class="chart-svg" role="img" '
        f'aria-label="Latência p95 por endpoint">',
        '<text x="260" y="18" font-size="11" fill="#64748b">Latência p95 e Média (ms)</text>',
    ]

    for idx, ep in enumerate(top):
        y = 30 + idx * row_h
        label = html.escape(f"{ep['method']} {ep['endpoint']}")
        if len(label) > 34:
            label = label[:31] + "..."
        p95_w = max(2.0, (ep["p95_ms"] / max_p95) * bar_max_w)
        avg_w = max(2.0, (ep["avg_ms"] / max_p95) * bar_max_w)
        bar_color = "#ef4444" if ep["error_rate_pct"] > 0 else "#2563eb"

        svg_parts.append(
            f'<text x="8" y="{y + 16}" font-size="12" fill="#1e293b" font-family="monospace">{label}</text>'
        )
        svg_parts.append(
            f'<rect x="{label_w}" y="{y + 3}" width="{p95_w:.1f}" height="18" rx="4" fill="{bar_color}" opacity="0.28" />'
        )
        svg_parts.append(
            f'<rect x="{label_w}" y="{y + 3}" width="{avg_w:.1f}" height="18" rx="4" fill="{bar_color}" />'
        )
        svg_parts.append(
            f'<text x="{label_w + p95_w + 8:.1f}" y="{y + 16}" font-size="11" fill="#334155">'
            f'avg {ep["avg_ms"]:.0f}ms | p95 {ep["p95_ms"]:.0f}ms</text>'
        )

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


def _build_timeseries_svg(series: list[dict[str, Any]]) -> str:
    if not series:
        return "<p>Série temporal indisponível.</p>"

    width = 760
    height = 240
    pad_l, pad_r, pad_t, pad_b = 54, 54, 24, 42
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b

    max_rps = max((pt["rps"] for pt in series), default=1.0) or 1.0
    max_p95 = max((pt["p95_ms"] for pt in series), default=1.0) or 1.0

    n = len(series)
    step_x = plot_w / max(1, n - 1) if n > 1 else 0.0

    rps_points: list[str] = []
    p95_points: list[str] = []
    labels: list[str] = []

    for i, pt in enumerate(series):
        x = pad_l + (i * step_x if n > 1 else plot_w / 2)
        y_rps = pad_t + plot_h - (pt["rps"] / max_rps) * plot_h
        y_p95 = pad_t + plot_h - (pt["p95_ms"] / max_p95) * plot_h
        rps_points.append(f"{x:.1f},{y_rps:.1f}")
        p95_points.append(f"{x:.1f},{y_p95:.1f}")
        if n <= 12 or i % max(1, n // 8) == 0 or i == n - 1:
            labels.append(
                f'<text x="{x:.1f}" y="{height - 12}" text-anchor="middle" '
                f'font-size="10" fill="#64748b">{html.escape(pt["label"])}</text>'
            )

    svg = [
        f'<svg viewBox="0 0 {width} {height}" class="chart-svg" role="img" '
        f'aria-label="Evolução temporal de RPS e Latência p95">',
        f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{pad_t + plot_h}" stroke="#cbd5e1" />',
        f'<line x1="{pad_l}" y1="{pad_t + plot_h}" x2="{pad_l + plot_w}" y2="{pad_t + plot_h}" stroke="#cbd5e1" />',
        f'<line x1="{pad_l + plot_w}" y1="{pad_t}" x2="{pad_l + plot_w}" y2="{pad_t + plot_h}" stroke="#cbd5e1" />',
        f'<text x="{pad_l - 6}" y="{pad_t + 8}" text-anchor="end" font-size="10" fill="#2563eb">{max_rps:.1f} RPS</text>',
        f'<text x="{pad_l + plot_w + 6}" y="{pad_t + 8}" text-anchor="start" font-size="10" fill="#f59e0b">{max_p95:.0f} ms</text>',
    ]
    if len(rps_points) > 1:
        svg.append(
            f'<polyline fill="none" stroke="#2563eb" stroke-width="2.5" points="{" ".join(rps_points)}" />'
        )
        svg.append(
            f'<polyline fill="none" stroke="#f59e0b" stroke-width="2.5" stroke-dasharray="5,3" points="{" ".join(p95_points)}" />'
        )
    for pt_str in rps_points:
        cx, cy = pt_str.split(",")
        svg.append(f'<circle cx="{cx}" cy="{cy}" r="3.5" fill="#2563eb" />')
    for pt_str in p95_points:
        cx, cy = pt_str.split(",")
        svg.append(f'<circle cx="{cx}" cy="{cy}" r="3.5" fill="#f59e0b" />')
    svg.extend(labels)
    svg.append("</svg>")
    return "\n".join(svg)


def render_html_report(summary: dict[str, Any]) -> str:
    """Renderiza relatório HTML autocontido com gráficos SVG."""
    meta = summary["metadata"]
    g = summary["global"]
    sla = summary["sla"]
    badge_cls = "badge-pass" if sla["passed"] else "badge-fail"
    badge_txt = "SLA APROVADO" if sla["passed"] else "SLA REPROVADO"

    ep_rows = []
    for ep in summary["endpoints"]:
        err_cls = "text-danger" if ep["failures"] > 0 else "text-ok"
        ep_rows.append(
            "<tr>"
            f"<td><code>{html.escape(ep['method'])}</code></td>"
            f"<td><code>{html.escape(ep['endpoint'])}</code></td>"
            f"<td>{ep['requests']}</td>"
            f"<td class='{err_cls}'>{ep['failures']} ({ep['error_rate_pct']:.2f}%)</td>"
            f"<td>{ep['rps']:.2f}</td>"
            f"<td>{ep['min_ms']:.2f}</td>"
            f"<td>{ep['avg_ms']:.2f}</td>"
            f"<td>{ep['p50_ms']:.2f}</td>"
            f"<td><strong>{ep['p95_ms']:.2f}</strong></td>"
            f"<td>{ep['p99_ms']:.2f}</td>"
            f"<td>{ep['max_ms']:.2f}</td>"
            "</tr>"
        )

    sla_rows = []
    for chk in sla["checks"]:
        cls = "badge-pass" if chk["passed"] else "badge-fail"
        lbl = "Aprovado" if chk["passed"] else "Reprovado"
        sla_rows.append(
            "<tr>"
            f"<td>{html.escape(chk['criterion'])}</td>"
            f"<td><strong>{html.escape(chk['measured'])}</strong></td>"
            f"<td><span class='badge {cls}'>{lbl}</span></td>"
            "</tr>"
        )

    diag_items = "".join(f"<li>{html.escape(note)}</li>" for note in summary["diagnostics"])
    status_items = "".join(
        f"<tr><td><code>{html.escape(k)}</code></td><td>{v}</td>"
        f"<td>{(v / max(1, g['total_requests']) * 100):.2f}%</td></tr>"
        for k, v in summary["status_codes"].items()
    )

    errors_block = ""
    if summary["top_errors"]:
        err_rows = "".join(
            f"<tr><td><code>{html.escape(e['message'])}</code></td><td>{e['count']}</td></tr>"
            for e in summary["top_errors"]
        )
        errors_block = (
            "<section class='card'><h2>Principais Erros</h2>"
            "<table><thead><tr><th>Erro</th><th>Ocorrências</th></tr></thead>"
            f"<tbody>{err_rows}</tbody></table></section>"
        )

    return f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Relatório de Teste de Carga — TaskFlow</title>
  <style>
    :root {{
      --bg: #f8fafc;
      --card: #ffffff;
      --text: #0f172a;
      --muted: #475569;
      --border: #e2e8f0;
      --accent: #2563eb;
      --pass: #15803d;
      --pass-bg: #dcfce7;
      --fail: #b91c1c;
      --fail-bg: #fee2e2;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      padding: 28px;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
    }}
    .container {{ max-width: 1180px; margin: 0 auto; }}
    header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      flex-wrap: wrap;
      gap: 16px;
      margin-bottom: 24px;
    }}
    h1 {{ margin: 0 0 6px; font-size: 1.75rem; }}
    h2 {{ margin: 0 0 14px; font-size: 1.15rem; color: var(--text); }}
    .meta {{ color: var(--muted); font-size: 0.92rem; }}
    .badge {{
      display: inline-block;
      padding: 6px 12px;
      border-radius: 999px;
      font-weight: 700;
      font-size: 0.85rem;
    }}
    .badge-pass {{ background: var(--pass-bg); color: var(--pass); }}
    .badge-fail {{ background: var(--fail-bg); color: var(--fail); }}
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(175px, 1fr));
      gap: 14px;
      margin-bottom: 22px;
    }}
    .kpi {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 14px 16px;
    }}
    .kpi-label {{ font-size: 0.8rem; color: var(--muted); text-transform: uppercase; letter-spacing: .04em; }}
    .kpi-value {{ font-size: 1.5rem; font-weight: 700; margin-top: 4px; }}
    .card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 18px 20px;
      margin-bottom: 20px;
      overflow-x: auto;
    }}
    .grid-2 {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
      gap: 18px;
    }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
    th, td {{ padding: 9px 10px; border-bottom: 1px solid var(--border); text-align: left; }}
    th {{ background: #f1f5f9; font-weight: 600; color: #334155; }}
    .text-danger {{ color: var(--fail); font-weight: 600; }}
    .text-ok {{ color: var(--pass); }}
    .chart-svg {{ width: 100%; height: auto; display: block; }}
    .legend {{ font-size: 0.85rem; color: var(--muted); margin-bottom: 8px; }}
    code {{ background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-size: 0.85em; }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div>
        <h1>Relatório de Teste de Carga — TaskFlow</h1>
        <div class="meta">
          Executado em <strong>{html.escape(str(meta['executed_at']))}</strong> |
          Modo: <code>{html.escape(str(meta['mode']))}</code> |
          Alvo: <code>{html.escape(str(meta['target_url']))}</code> |
          Banco: <code>{html.escape(str(meta['database_engine']))}</code> |
          VUs: <strong>{meta['users']}</strong> |
          Duração: <strong>{meta['duration_seconds']}s</strong>
        </div>
      </div>
      <span class="badge {badge_cls}">{badge_txt}</span>
    </header>

    <section class="kpi-grid">
      <div class="kpi"><div class="kpi-label">Total Requisições</div><div class="kpi-value">{g['total_requests']}</div></div>
      <div class="kpi"><div class="kpi-label">Vazão Média (RPS)</div><div class="kpi-value">{g['rps']:.2f}/s</div></div>
      <div class="kpi"><div class="kpi-label">Taxa de Erros</div><div class="kpi-value">{g['error_rate_pct']:.2f}%</div></div>
      <div class="kpi"><div class="kpi-label">Latência Média</div><div class="kpi-value">{g['avg_ms']:.1f} ms</div></div>
      <div class="kpi"><div class="kpi-label">Percentil p95</div><div class="kpi-value">{g['p95_ms']:.1f} ms</div></div>
      <div class="kpi"><div class="kpi-label">Percentil p99</div><div class="kpi-value">{g['p99_ms']:.1f} ms</div></div>
    </section>

    <div class="grid-2">
      <section class="card">
        <h2>Critérios de SLA</h2>
        <table>
          <thead><tr><th>Critério</th><th>Medido</th><th>Status</th></tr></thead>
          <tbody>{''.join(sla_rows)}</tbody>
        </table>
      </section>
      <section class="card">
        <h2>Códigos HTTP</h2>
        <table>
          <thead><tr><th>Código</th><th>Quantidade</th><th>%</th></tr></thead>
          <tbody>{status_items}</tbody>
        </table>
      </section>
    </div>

    <section class="card">
      <h2>Evolução Temporal (RPS vs. Latência p95)</h2>
      <div class="legend">Linha azul sólida: RPS | Linha laranja tracejada: p95 (ms)</div>
      {_build_timeseries_svg(summary['time_series'])}
    </section>

    <section class="card">
      <h2>Latência por Endpoint (Média vs. p95)</h2>
      {_build_endpoint_bar_svg(summary['endpoints'])}
    </section>

    <section class="card">
      <h2>Detalhamento por Endpoint</h2>
      <table>
        <thead>
          <tr>
            <th>Método</th><th>Endpoint</th><th>Req.</th><th>Falhas</th><th>RPS</th>
            <th>Mín</th><th>Média</th><th>p50</th><th>p95</th><th>p99</th><th>Máx</th>
          </tr>
        </thead>
        <tbody>{''.join(ep_rows)}</tbody>
      </table>
    </section>

    {errors_block}

    <section class="card">
      <h2>Diagnóstico Automático e Recomendações</h2>
      <ul>{diag_items}</ul>
    </section>
  </div>
</body>
</html>
"""


def write_reports(summary: dict[str, Any], output_dir: Path, timestamp_tag: str) -> dict[str, Path]:
    """Grava os relatórios em Markdown, HTML e JSON (com cópias *_latest)."""
    output_dir.mkdir(parents=True, exist_ok=True)

    md_content = render_markdown_report(summary)
    html_content = render_html_report(summary)
    json_content = json.dumps(summary, indent=2, ensure_ascii=False)

    paths = {
        "markdown": output_dir / f"relatorio_carga_{timestamp_tag}.md",
        "markdown_latest": output_dir / "relatorio_carga_latest.md",
        "html": output_dir / f"relatorio_carga_{timestamp_tag}.html",
        "html_latest": output_dir / "relatorio_carga_latest.html",
        "json": output_dir / f"relatorio_carga_{timestamp_tag}.json",
        "json_latest": output_dir / "relatorio_carga_latest.json",
    }

    paths["markdown"].write_text(md_content, encoding="utf-8")
    paths["markdown_latest"].write_text(md_content, encoding="utf-8")
    paths["html"].write_text(html_content, encoding="utf-8")
    paths["html_latest"].write_text(html_content, encoding="utf-8")
    paths["json"].write_text(json_content, encoding="utf-8")
    paths["json_latest"].write_text(json_content, encoding="utf-8")

    return paths
