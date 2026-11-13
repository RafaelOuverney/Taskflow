# Relatório Unificado de Testes Caixa-Branca — TaskFlow

**Executado em:** 12/11/2026 19:56:35  
**Duração Total da Suíte:** 4.09 s  
**Status Geral:** **APROVADO**

---

## 1. Sumário Executivo

| Indicador | Valor |
| :--- | ---: |
| Total de Casos de Teste | **34** |
| Aprovados (`PASS`) | **34** (100.00%) |
| Falhas (`FAIL`) | 0 |
| Erros (`ERROR`) | 0 |
| Ignorados (`SKIP`) | 0 |
| Cobertura Global de Linhas Executáveis | **1187/1258 (94.36%)** |

---

## 2. Resultados Consolidados por Módulo de Teste

| Módulo / Escopo | Total | Pass | Fail | Error | Duração (ms) | Status |
| :--- | ---: | ---: | ---: | ---: | ---: | :---: |
| ia (models, forms, services e views) | 10 | 10 | 0 | 0 | 645.47 | **Aprovado** |
| pages (autenticação, cadastro e perfil) | 5 | 5 | 0 | 0 | 779.85 | **Aprovado** |
| pages (models, forms, filters, mixins, templatetags) | 8 | 8 | 0 | 0 | 573.51 | **Aprovado** |
| pages (dashboard, cadernos, tarefas, subtarefas, anti-IDOR) | 5 | 5 | 0 | 0 | 673.61 | **Aprovado** |
| pages (equipes, RBAC e painel analítico) | 3 | 3 | 0 | 0 | 617.09 | **Aprovado** |
| Taskflow (urls, settings, wsgi, asgi) | 3 | 3 | 0 | 0 | 1.34 | **Aprovado** |

---

## 3. Cobertura Estrutural de Código por Arquivo

| App | Arquivo | Linhas Executáveis | Linhas Cobertas | Não Cobertas | Cobertura |
| :--- | :--- | ---: | ---: | ---: | ---: |
| `pages` | `pages/models.py` | 69 | 69 | 0 | **100.00%** |
| `pages` | `pages/views.py` | 623 | 567 | 56 | **91.01%** |
| `pages` | `pages/forms.py` | 45 | 45 | 0 | **100.00%** |
| `pages` | `pages/filters.py` | 39 | 38 | 1 | **97.44%** |
| `pages` | `pages/mixins.py` | 14 | 14 | 0 | **100.00%** |
| `pages` | `pages/urls.py` | 33 | 33 | 0 | **100.00%** |
| `pages` | `pages/templatetags/query_params.py` | 14 | 14 | 0 | **100.00%** |
| `ia` | `ia/models.py` | 96 | 96 | 0 | **100.00%** |
| `ia` | `ia/views.py` | 134 | 127 | 7 | **94.78%** |
| `ia` | `ia/forms.py` | 21 | 21 | 0 | **100.00%** |
| `ia` | `ia/services.py` | 135 | 130 | 5 | **96.30%** |
| `ia` | `ia/urls.py` | 11 | 11 | 0 | **100.00%** |
| `Taskflow` | `Taskflow/urls.py` | 14 | 12 | 2 | **85.71%** |
| `Taskflow` | `Taskflow/wsgi.py` | 5 | 5 | 0 | **100.00%** |
| `Taskflow` | `Taskflow/asgi.py` | 5 | 5 | 0 | **100.00%** |
| **Total** | **Todos os módulos principais** | **1258** | **1187** | **71** | **94.36%** |

---

## 4. Matriz Completa dos Casos de Teste Caixa-Branca

| # | Módulo | Classe / Método | Objetivo Estrutural | Tempo (ms) | Status |
| ---: | :--- | :--- | :--- | ---: | :---: |
| 1 | `test_ia_module` | `IAModelsAndFormsWhiteBoxTests.test_ia_forms` | Valida IAConfigForm e UserQuotaUpdateForm. | 50.38 | **PASS** |
| 2 | `test_ia_module` | `IAModelsAndFormsWhiteBoxTests.test_quota_properties_and_singleton` | Verifica get_active_config, percentage_used (incluindo limite 0) e remaining_tokens. | 41.06 | **PASS** |
| 3 | `test_ia_module` | `IAServicesControlFlowWhiteBoxTests.test_estimate_tokens_boundaries` | test_estimate_tokens_boundaries | 38.49 | **PASS** |
| 4 | `test_ia_module` | `IAServicesControlFlowWhiteBoxTests.test_gemini_fallback_without_api_key` | Caminho 3: Gemini sem API Key gera resposta simulada, registra auditoria e debita cota. | 41.26 | **PASS** |
| 5 | `test_ia_module` | `IAServicesControlFlowWhiteBoxTests.test_gemini_http_success_and_http_error` | Caminho 4: Gemini com API Key (HTTP 200 com usageMetadata vs HTTP 429). | 42.71 | **PASS** |
| 6 | `test_ia_module` | `IAServicesControlFlowWhiteBoxTests.test_ia_disabled_path` | Caminho 1: IA desativada retorna erro imediato sem criar auditoria. | 42.63 | **PASS** |
| 7 | `test_ia_module` | `IAServicesControlFlowWhiteBoxTests.test_openai_and_custom_and_exceptions` | Caminhos 5, 6, 7 e 8: OpenAI (sem chave / 200 / erro), Custom e RequestException. | 47.76 | **PASS** |
| 8 | `test_ia_module` | `IAServicesControlFlowWhiteBoxTests.test_quota_exceeded_path` | Caminho 2: Cota mensal esgotada bloqueia chamada e registra auditoria quota_exceeded. | 41.67 | **PASS** |
| 9 | `test_ia_module` | `IAViewsWhiteBoxTests.test_assistente_chat_window_and_clear_isolation` | Verifica janela de 5 mensagens no AssistenteChatAPI e isolamento ao limpar histórico. | 151.68 | **PASS** |
| 10 | `test_ia_module` | `IAViewsWhiteBoxTests.test_config_requisicoes_consumo_views` | Verifica IAConfigView (GET/POST), IATestConnectionView, IARequisicoesView, IAConsumoUsuariosView e MeuConsumoView. | 147.83 | **PASS** |
| 11 | `test_pages_auth_profile` | `PagesAuthAndProfileWhiteBoxTests.test_cadastro_all_validation_branches` | Cobre todos os desvios de CadastroView: GET, campos faltando, nome < 3, senhas, termos, duplicado e sucesso. | 108.16 | **PASS** |
| 12 | `test_pages_auth_profile` | `PagesAuthAndProfileWhiteBoxTests.test_index_get_unauthenticated_and_authenticated_redirect` | GET / renderiza index para anônimo e redireciona para /dashboard/ quando autenticado. | 66.07 | **PASS** |
| 13 | `test_pages_auth_profile` | `PagesAuthAndProfileWhiteBoxTests.test_index_post_all_branches` | Cobre campos vazios (400), credenciais inválidas (401), rememberMe True/False (200) e JSON inválido (500). | 196.15 | **PASS** |
| 14 | `test_pages_auth_profile` | `PagesAuthAndProfileWhiteBoxTests.test_perfil_and_alterar_senha_branches` | Cobre PerfilView e os caminhos de erro/sucesso em AlterarSenhaView. | 343.82 | **PASS** |
| 15 | `test_pages_auth_profile` | `PagesAuthAndProfileWhiteBoxTests.test_public_pages_and_logout` | Verifica RecuperacaoView, SobreView e LogoutView. | 65.65 | **PASS** |
| 16 | `test_pages_models_forms_filters` | `PagesFormsAndFiltersWhiteBoxTests.test_equipe_filter_branches` | Cobre filtragem por nome e privacidade em EquipeFilter. | 77.59 | **PASS** |
| 17 | `test_pages_models_forms_filters` | `PagesFormsAndFiltersWhiteBoxTests.test_forms_validation` | Valida caminhos válidos e inválidos de UserUpdateForm, ProfileUpdateForm, SecurityForm e EquipeForm. | 121.32 | **PASS** |
| 18 | `test_pages_models_forms_filters` | `PagesFormsAndFiltersWhiteBoxTests.test_group_required_mixin_all_paths` | Testa os 3 ramos de GroupRequiredMixin: anônimo, usuário comum e membro de Admins. | 78.10 | **PASS** |
| 19 | `test_pages_models_forms_filters` | `PagesFormsAndFiltersWhiteBoxTests.test_param_replace_templatetag` | Testa substituição, adição, remoção e contexto sem request no param_replace. | 72.67 | **PASS** |
| 20 | `test_pages_models_forms_filters` | `PagesFormsAndFiltersWhiteBoxTests.test_task_filter_branches` | Cobre todos os ramos de TaskFilter.filter_completed ('true', 'false', vazio) e busca. | 76.35 | **PASS** |
| 21 | `test_pages_models_forms_filters` | `PagesModelsWhiteBoxTests.test_equipe_str_and_m2m` | Verifica criação de Equipe, privacidade padrão e associação M2M. | 71.85 | **PASS** |
| 22 | `test_pages_models_forms_filters` | `PagesModelsWhiteBoxTests.test_notebook_str_and_defaults` | Verifica valores padrão e representação textual de Notebook. | 35.98 | **PASS** |
| 23 | `test_pages_models_forms_filters` | `PagesModelsWhiteBoxTests.test_task_subtask_properties_and_ordering` | Verifica propriedades subtasks_count/subtasks_completed e ordenação de SubTask. | 39.65 | **PASS** |
| 24 | `test_pages_notebooks_tasks` | `PagesNotebooksTasksWhiteBoxTests.test_csrf_enforced_on_sensitive_post` | Garante que Client(enforce_csrf_checks=True) bloqueia POST sem token CSRF (403). | 101.84 | **PASS** |
| 25 | `test_pages_notebooks_tasks` | `PagesNotebooksTasksWhiteBoxTests.test_dashboard_and_calendar_views` | Verifica contexto do DashboardView (gráfico 7 dias e contadores) e CalendarView. | 119.50 | **PASS** |
| 26 | `test_pages_notebooks_tasks` | `PagesNotebooksTasksWhiteBoxTests.test_notebook_views_and_anti_idor` | Verifica criação, salvamento, listagem, exclusão e bloqueio IDOR em cadernos. | 159.85 | **PASS** |
| 27 | `test_pages_notebooks_tasks` | `PagesNotebooksTasksWhiteBoxTests.test_tasks_and_subtasks_crud_and_anti_idor` | Verifica CRUD completo de Task/SubTask e bloqueio estrito de IDOR (404/403). | 167.39 | **PASS** |
| 28 | `test_pages_notebooks_tasks` | `PagesNotebooksTasksWhiteBoxTests.test_tasks_list_view_pagination_and_orm_queries` | Verifica paginação (5 por página) e comportamento das consultas em TasksListView/TasksGetListAPI. | 125.03 | **PASS** |
| 29 | `test_pages_teams_analytics` | `PagesTeamsAndAnalyticsWhiteBoxTests.test_analise_view_rbac_and_metrics_calculation` | Verifica bloqueio RBAC para não-Admins e cálculo de métricas agregadas em AnaliseView. | 199.85 | **PASS** |
| 30 | `test_pages_teams_analytics` | `PagesTeamsAndAnalyticsWhiteBoxTests.test_equipe_detail_create_update_delete_permissions` | Verifica controle de acesso: membro lê detalhe, mas só owner edita/exclui. | 217.10 | **PASS** |
| 31 | `test_pages_teams_analytics` | `PagesTeamsAndAnalyticsWhiteBoxTests.test_equipe_list_visibility_and_query_optimization` | Verifica que EquipeListView mantém número constante de queries (sem N+1) ao crescer o número de equipes. | 200.14 | **PASS** |
| 32 | `test_core_taskflow` | `CoreTaskflowWhiteBoxTests.test_security_and_session_configuration` | Verifica flags de segurança de sessão e prioridade do Argon2PasswordHasher. | 0.27 | **PASS** |
| 33 | `test_core_taskflow` | `CoreTaskflowWhiteBoxTests.test_url_resolution_across_apps` | Confirma que todas as rotas principais resolvem para suas respectivas views. | 0.85 | **PASS** |
| 34 | `test_core_taskflow` | `CoreTaskflowWhiteBoxTests.test_wsgi_and_asgi_entrypoints` | Garante que os objetos application WSGI e ASGI são chamáveis válidos. | 0.22 | **PASS** |
