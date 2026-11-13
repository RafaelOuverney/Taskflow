# Relatório de Teste de Carga — TaskFlow

**Executado em:** 12/11/2026 20:17:32  
**Modo de Execução:** standalone  
**URL Alvo:** `http://127.0.0.1:50777`  
**Banco de Dados:** `sqlite3 (temporário)`  
**Usuários Virtuais (VUs):** 30 | **Duração:** 30s | **Ramp-up:** 5.0s  
**Status Geral (SLA):** **REPROVADO**

---

## 1. Sumário Executivo (Métricas Globais)

| Métrica | Valor Medido |
| :--- | ---: |
| Total de Requisições | **811** |
| Requisições com Sucesso | 807 |
| Falhas | 4 (0.49%) |
| Duração Efetiva | 30.94 s |
| Vazão Média (RPS) | **26.21 req/s** |
| Latência Mínima | 14.30 ms |
| Latência Média | 820.44 ms |
| Mediana (p50) | 427.21 ms |
| Percentil p90 | 1806.73 ms |
| Percentil p95 | **3194.35 ms** |
| Percentil p99 | **5941.19 ms** |
| Latência Máxima | 7784.25 ms |
| Desvio Padrão | 1167.83 ms |
| Tráfego Recebido | 21097.39 KB (681.82 KB/s) |

### Avaliação de Critérios de SLA

| Critério | Valor Medido | Resultado |
| :--- | ---: | :---: |
| Taxa de erro global <= 2.00% | 0.49% | **Aprovado** |
| Latência p95 global <= 1000 ms | 3194.35 ms | **Reprovado** |
| Latência p99 global <= 2000 ms | 5941.19 ms | **Reprovado** |

---

## 2. Desempenho Detalhado por Endpoint

| Método | Endpoint | Req. | Falhas | Erro % | RPS | Mín (ms) | Média (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Máx (ms) |
| :---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `POST` | `/api/notebook/save/` | 143 | 0 | 0.00% | 4.62 | 20.89 | 630.27 | 330.99 | 2876.40 | 4382.53 | 5117.29 |
| `GET` | `/dashboard/` | 124 | 2 | 1.61% | 4.01 | 44.77 | 1549.63 | 1085.80 | 4911.34 | 7503.48 | 7784.25 |
| `GET` | `/api/task/list/` | 92 | 1 | 1.09% | 2.97 | 22.56 | 1046.21 | 647.95 | 4397.54 | 7044.69 | 7073.97 |
| `GET` | `/tarefas/` | 76 | 0 | 0.00% | 2.46 | 25.72 | 545.91 | 344.23 | 1332.61 | 5083.42 | 5660.85 |
| `GET` | `/caderno/` | 64 | 0 | 0.00% | 2.07 | 22.52 | 734.22 | 386.48 | 2683.70 | 6103.10 | 6372.92 |
| `GET` | `/tarefas/?priority=high&completed=false` | 63 | 0 | 0.00% | 2.04 | 30.95 | 611.71 | 308.13 | 2442.64 | 4266.92 | 5502.84 |
| `POST` | `/api/task/toggle/` | 51 | 1 | 1.96% | 1.65 | 21.09 | 848.94 | 332.14 | 4552.54 | 6004.98 | 6980.68 |
| `GET` | `/equipes/` | 39 | 0 | 0.00% | 1.26 | 42.70 | 966.10 | 490.10 | 4405.15 | 5268.35 | 5746.65 |
| `GET` | `/` | 30 | 0 | 0.00% | 0.97 | 14.30 | 31.84 | 28.24 | 56.20 | 76.86 | 83.58 |
| `POST` | `/` | 30 | 0 | 0.00% | 0.97 | 57.14 | 321.36 | 200.91 | 976.60 | 2223.88 | 2608.84 |
| `POST` | `/api/task/create/` | 30 | 0 | 0.00% | 0.97 | 33.98 | 289.96 | 232.17 | 587.34 | 1087.73 | 1283.02 |
| `GET` | `/equipes/<id>/` | 26 | 0 | 0.00% | 0.84 | 48.27 | 935.33 | 605.15 | 1968.39 | 4754.63 | 5647.18 |
| `GET` | `/ia/meu-consumo/` | 23 | 0 | 0.00% | 0.74 | 60.16 | 746.81 | 348.51 | 2345.74 | 5146.93 | 5910.18 |
| `GET` | `/analise/?equipe=<id>` | 20 | 0 | 0.00% | 0.65 | 61.94 | 903.15 | 830.91 | 1785.87 | 2230.13 | 2341.20 |

---

## 3. Distribuição de Códigos de Status HTTP

| Código HTTP | Quantidade | Participação |
| :---: | ---: | ---: |
| `200` | 807 | 99.51% |
| `400` | 3 | 0.37% |
| `500` | 1 | 0.12% |

### Principais Erros Registrados

| Mensagem / Causa | Ocorrências |
| :--- | ---: |
| `HTTP 400 em GET /dashboard/` | 2 |
| `HTTP 500 em POST /api/task/toggle/` | 1 |
| `HTTP 400 em GET /api/task/list/` | 1 |

---

## 4. Evolução Temporal da Carga

| Janela | Requisições | Falhas | RPS | Latência Média (ms) | p95 (ms) |
| :---: | ---: | ---: | ---: | ---: | ---: |
| 0-2s | 59 | 0 | 29.50 | 55.91 | 113.26 |
| 2-4s | 67 | 0 | 33.50 | 309.18 | 779.64 |
| 4-6s | 58 | 0 | 29.00 | 545.10 | 1667.18 |
| 6-8s | 49 | 0 | 24.50 | 835.68 | 2144.96 |
| 8-10s | 52 | 0 | 26.00 | 676.92 | 2074.19 |
| 10-12s | 54 | 2 | 27.00 | 1061.86 | 4491.10 |
| 12-14s | 51 | 0 | 25.50 | 988.62 | 3853.30 |
| 14-16s | 53 | 0 | 26.50 | 744.39 | 2725.89 |
| 16-18s | 50 | 0 | 25.00 | 904.36 | 3841.38 |
| 18-20s | 59 | 0 | 29.50 | 828.56 | 2805.84 |
| 20-22s | 47 | 1 | 23.50 | 1202.64 | 5457.55 |
| 22-24s | 43 | 0 | 21.50 | 972.13 | 2704.48 |
| 24-26s | 51 | 0 | 25.50 | 1035.63 | 3470.92 |
| 26-28s | 51 | 1 | 25.50 | 874.39 | 3720.20 |
| 28-30.9s | 67 | 0 | 22.77 | 1441.03 | 5056.97 |

---

## 5. Diagnóstico Automático e Recomendações

- Taxa de erro global de 0.49% (4 falhas em 811 requisições).
- Endpoint com maior latência p95: `GET /dashboard/` (p95 = 4911.34 ms, média = 1549.63 ms).
- Endpoint mais demandado: `POST /api/notebook/save/` com 143 requisições (4.62 req/s).
- Django Debug Toolbar ativo durante o benchmark (DEBUG=True), adicionando overhead de instrumentação às respostas HTML. Em produção (DEBUG=False), a latência tende a ser menor.
