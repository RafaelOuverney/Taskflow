# 🤖 AGENTS.md - Diretrizes para Agentes de IA no TaskFlow

Este documento define a governança, convenções e capacidades dos Agentes Autônomos de Inteligência Artificial que operam no desenvolvimento e manutenção do projeto **TaskFlow**.

---

## 🧭 Princípios Fundamentais

1. **Segurança e Isolamento de Dados**:
   - Nenhum dado pertencente a um usuário pode ser exposto, alterado ou excluído por outro usuário sem permissão expressa.
   - Qualquer operação de banco de dados (`get`, `filter`, `update`, `delete`) em entidades de usuários (`Notebook`, `Task`, etc.) deve conter restrição de propriedade (`owner=request.user`).

2. **Performance e Otimização do ORM**:
   - Evitar o problema de queries $N+1$.
   - Utilizar `select_related` para relações 1-para-1 ou N-para-1 (`ForeignKey`).
   - Utilizar `prefetch_related` para relações N-para-N (`ManyToManyField`) ou relacionamentos inversos.
   - Monitorar a contagem de queries através do **Django Debug Toolbar**.

3. **Padronização e Qualidade de Código**:
   - Seguir PEP 8 e convenções idiomáticas do Django.
   - Manter as mensagens de commit alinhadas com a especificação **Conventional Commits**.
   - Garantir que migrações de banco estejam sempre sincronizadas com os modelos.

---

## 🛠️ Catálogo de Skills dos Agentes

Os agentes que atuam neste projeto possuem acesso às seguintes habilidades especializadas:

| Skill | Localização | Finalidade |
|---|---|---|
| **commit-convention** | `.agents/skills/commit-convention/SKILL.md` | Padroniza mensagens de commit no padrão Conventional Commits com escopos e regras de validação. |
| **django-query-optimizer** | `.agents/skills/django-query-optimizer/SKILL.md` | Identifica gargalos de consulta, $N+1$ queries no ORM e aplica `select_related` / `prefetch_related`. |
| **multi-tenant-security** | `.agents/skills/multi-tenant-security/SKILL.md` | Garante a validação de acesso e propriedade estrita de registros por usuário em Views e APIs. |

---

## 🔄 Fluxo de Trabalho do Agente

1. **Análise de Requisitos**: Ler o contexto da solicitação e os modelos envolvidos.
2. **Execução Segura**: Testar queries, garantir proteção CSRF e autenticação.
3. **Verificação de Performance**: Checar queries adicionadas com o Django Debug Toolbar.
4. **Commit Padronizado**: Utilizar a skill `commit-convention` para registrar a entrega.

