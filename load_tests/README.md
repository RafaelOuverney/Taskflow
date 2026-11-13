# Teste de Carga — TaskFlow

Suíte de teste de carga concorrente para a aplicação **TaskFlow**, com geração automática de relatórios em **Markdown**, **HTML** (com gráficos SVG) e **JSON**.

## Estrutura

- [run_load_test.py](run_load_test.py): Executor multiusuário (`ThreadPoolExecutor` + `requests.Session`), mantendo cookies de sessão e rotação automática de token CSRF (`X-CSRFToken`).
- [server.py](server.py): Sobe uma instância isolada do TaskFlow (`ThreadedWSGIServer` + banco SQLite temporário) com usuários, cadernos, tarefas, subtarefas e equipes populados automaticamente, sem alterar o `db.sqlite3` do projeto.
- [metrics.py](metrics.py): Cálculo de vazão (RPS), percentis de latência (`p50`, `p90`, `p95`, `p99`), série temporal por janela, diagnóstico automático e verificação de SLA.
- [report.py](report.py): Geração dos relatórios em `load_tests/reports/`.

## Como Executar

### 1. Modo isolado (padrão — não exige servidor prévio)

```powershell
.venv\Scripts\python.exe load_tests\run_load_test.py --users 20 --duration 20 --ramp-up 3
```

Opções úteis no modo isolado:
- `--sqlite-wal`: ativa `PRAGMA journal_mode=WAL` e `timeout=20` no SQLite temporário.
- `--no-debug-toolbar`: desabilita o Django Debug Toolbar para medir a latência sem overhead de depuração.
- `--strict-sla`: retorna código de saída `1` se algum critério de SLA falhar (útil para CI/CD).

### 2. Modo servidor externo (ex.: PostgreSQL / Gunicorn / `runserver`)

```powershell
.venv\Scripts\python.exe load_tests\run_load_test.py --url http://127.0.0.1:8000 --users 25 --duration 30 --ramp-up 5
```

No modo externo, cada usuário virtual realiza cadastro automático via `POST /cadastro/`, cria um caderno e uma tarefa inicial e executa o fluxo ponderado contra o servidor alvo.

## Fluxos Simulados

| Método | Endpoint | Cenário |
| :---: | :--- | :--- |
| `GET/POST` | `/` | Aquisição de token CSRF e autenticação |
| `GET` | `/dashboard/` | Painel consolidado e gráfico semanal |
| `GET` | `/tarefas/` e `/tarefas/?priority=high&completed=false` | Listagem paginada e filtragem (`TaskFilter`) |
| `GET` | `/api/task/list/` | Listagem JSON de tarefas e subtarefas |
| `POST` | `/api/task/create/` e `/api/task/toggle/` | Criação e alternância de status de tarefas |
| `GET` | `/caderno/` | Carregamento do editor de cadernos |
| `POST` | `/api/notebook/save/` | Simulação de *auto-save* contínuo |
| `GET` | `/equipes/` e `/equipes/<id>/` | Listagem e detalhes de equipes |
| `GET` | `/analise/?equipe=<id>` | Painel analítico gerencial |
| `GET` | `/ia/meu-consumo/` | Monitoramento de cota de IA |

## Relatórios Gerados

Ao final de cada execução, os seguintes arquivos são gravados em `load_tests/reports/`:
- `relatorio_carga_<timestamp>.md` e `relatorio_carga_latest.md`
- `relatorio_carga_<timestamp>.html` e `relatorio_carga_latest.html`
- `relatorio_carga_<timestamp>.json` e `relatorio_carga_latest.json`
