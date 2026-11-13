---
name: multi-tenant-security
description: Garante o isolamento estrito de dados entre usuários no Django, prevenindo falhas de IDOR e vazamento de informações.
---

# Skill: Segurança e Isolamento de Registros por Usuário

Esta skill orienta o agente a implementar salvaguardas rigorosas para que cada usuário acesse, altere e exclua estritamente seus próprios registros.

## Regras de Implementação

### 1. ListViews e Querysets
Sempre redefinir `get_queryset()` nas views para restringir à chave do usuário autenticado:
```python
class TaskListView(LoginRequiredMixin, ListView):
    def get_queryset(self):
        # NUNCA usar Task.objects.all() sem filtro de usuário
        return Task.objects.filter(owner=self.request.user)
```

### 2. UpdateView e DeleteView
Nunca confiar apenas no parâmetro `pk` ou `id` da URL. O queryset base da view deve conter a restrição de propriedade:
```python
class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    def get_queryset(self):
        # Retorna 404 automaticamente se o ID pertencer a outro usuário
        return Task.objects.filter(owner=self.request.user)
```

### 3. CreateView
Ao salvar um novo registro, atribuir programaticamente o usuário da requisição antes da persistência:
```python
def form_valid(self, form):
    form.instance.owner = self.request.user
    return super().form_valid(form)
```

### 4. APIs e Endpoints AJAX
Em requisições POST/DELETE que recebem `id` via corpo JSON ou FormData:
```python
# Correto:
registro = get_object_or_404(Model, id=item_id, owner=request.user)

# Incorreto (Vulnerabilidade IDOR):
registro = Model.objects.get(id=item_id)
registro.delete()
```

