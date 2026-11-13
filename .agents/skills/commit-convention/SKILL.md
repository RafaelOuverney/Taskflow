---
name: commit-convention
description: Padroniza as mensagens de commit no projeto TaskFlow seguindo a convenção Conventional Commits.
---

# Skill: Padronização de Mensagens de Commit

Esta skill orienta o agente a criar e formatar mensagens de commit claras, consistentes e rastreáveis para o repositório TaskFlow.

## Estrutura do Commit

```text
<tipo>(<escopo>): <descrição no imperativo e em minúsculas>

[corpo opcional explicando o motivo da mudança e detalhes técnicos]

[rodapé opcional com referências a issues ou breaking changes]
```

## Tipos Permitidos

* `feat`: Introdução de uma nova funcionalidade no sistema (ex: nova view, novo modelo).
* `fix`: Correção de um bug ou comportamento inesperado.
* `refactor`: Refatoração de código que não altera o comportamento externo (ex: modularização).
* `perf`: Mudança focada em performance (ex: adição de `select_related` para mitigar $N+1$).
* `style`: Ajustes de formatação, espaços, lint ou imports (sem mudança de lógica).
* `test`: Adição ou correção de testes automatizados.
* `docs`: Alterações na documentação (`readme.md`, `AGENTS.md`, docstrings).
* `build`: Alterações em dependências, scripts de build ou empacotamento (`requirements.txt`).
* `ci`: Ajustes de pipelines de CI/CD ou arquivos de deploy (`app.yaml`).

## Escopos Recomendados

* `tasks`: Módulo de tarefas e subtarefas.
* `notebook`: Módulo de anotações/caderno.
* `equipes`: Módulo de equipes e permissões de grupos.
* `ia`: Módulo de inteligência artificial, auditoria e assistente.
* `auth`: Login, cadastro, sessão e recuperação de senha.
* `deps`: Dependências do projeto.
* `deploy`: Configurações de nuvem (App Engine, Docker, etc.).

## Boas Práticas

1. Primeira linha com no máximo 72 caracteres.
2. Não colocar ponto final no título do commit.
3. Usar verbos no presente/imperativo ("adiciona", "corrige", "implementa", e não "adicionado" ou "corrigido").
4. Nunca commitar arquivos de ambiente local (`.env`, `.venv`, `.sqlite3`).

