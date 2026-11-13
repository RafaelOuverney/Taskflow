---
name: django-query-optimizer
description: Identifica queries repetidas e problemas N+1 no Django ORM e aplica otimizações com select_related e prefetch_related.
---

# Skill: Otimização de Queries Django ORM

Esta skill orienta o agente na inspeção de consultas SQL e otimização de desempenho utilizando o Django Debug Toolbar.

## Quando usar cada otimização

### 1. `select_related(*fields)`
* **Mecanismo**: Realiza um `SQL JOIN` e inclui os campos do modelo relacionado no `SELECT`.
* **Uso Obrigatório**: Relacionamentos de chave estrangeira simples (`ForeignKey`) e 1-para-1 (`OneToOneField`).
* **Exemplo**:
  ```python
  # Ineficiente (N+1 queries ao iterar):
  equipes = Equipe.objects.all()
  for e in equipes:
      print(e.owner.username)

  # Otimizado (1 query com INNER JOIN):
  equipes = Equipe.objects.select_related('owner').all()
  ```

### 2. `prefetch_related(*lookups)`
* **Mecanismo**: Executa uma query adicional com cláusula `WHERE id IN (...)` e faz a junção dos objetos na memória do Python.
* **Uso Obrigatório**: Relacionamentos muitos-para-muitos (`ManyToManyField`) e relacionamentos inversos de chave estrangeira (`reverse ForeignKey`).
* **Exemplo**:
  ```python
  # Otimizando subtarefas e membros:
  tasks = Task.objects.filter(owner=user).prefetch_related('subtasks')
  equipes = Equipe.objects.prefetch_related('membros')
  ```

## Checklist de Validação com Django Debug Toolbar

1. Abrir a barra lateral do Django Debug Toolbar no navegador.
2. Acessar o painel **SQL**.
3. Verificar a quantidade total de consultas e alertas de **"Similar queries"** ou **"Duplicate queries"**.
4. Se o número de queries cresce proporcionalmente ao número de registros exibidos na página, trata-se de um gargalo $N+1$.
5. Aplicar o `select_related` ou `prefetch_related` no método `get_queryset()` da View e recarregar para confirmar a redução do número de queries para um valor constante pequeno (ex: 2 a 3 queries).

