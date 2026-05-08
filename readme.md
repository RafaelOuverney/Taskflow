# 📋 TaskFlow - Aplicação de Gerenciamento de Tarefas

Uma aplicação web moderna para gerenciamento de tarefas e notas, com autenticação segura, editor de texto WYSIWYG avançado e interface responsiva.

---

## 📌 Visão Geral

**TaskFlow** é uma plataforma de produtividade que combina:
- 🔐 **Autenticação Segura** - Login, cadastro e recuperação de senha
- 📝 **Editor de Notas** - Editor WYSIWYG com formatação em tempo real (negrito, itálico, links, etc.)
- 📊 **Dashboard** - Visualização rápida de estatísticas e tarefas
- 🎨 **Interface Moderna** - Design responsivo com barra lateral e componentes customizados
- ⚡ **Auto-save** - Salvamento automático de notas a cada 1.5s
- 🔔 **Notificações** - Sistema de toasts e modais customizados

---

## 🛠️ Tecnologias Utilizadas

### Backend
- **Django 6.0.3** - Framework web Python
  - Class-Based Views (CBV) para lógica de requisições
  - Autenticação integrada com User model
  - ORM para banco de dados
  - Sistema de sessões com cookies HTTP-only
  
- **Python 3.x**
  - Gerenciamento de senhas com Argon2 + PBKDF2
  - Middleware CSRF para segurança

- **SQLite3** - Banco de dados a ser alterado
  - Armazenamento de usuários, notas e sessões
  - Migrations automáticas com Django

### Frontend
- **HTML5** - Estrutura semântica
  - Contenteditable para editor WYSIWYG
  - Template engine Django ({% %})

- **CSS3** - Estilização
  - Variáveis CSS (:root) para tema consistente
  - Flexbox e Grid para layout responsivo
  - Animações suaves (fade, slide, etc.)
  - Design mobile-first com breakpoints

- **JavaScript Vanilla** - Interatividade
  - Sem dependências externas (jQuery, React, Vue)
  - Fetch API para requisições AJAX
  - document.execCommand() para formatação de texto
  - Event listeners para interações

- **Font Awesome 6.4.0** - Ícones
  - CDN para ícones consistentes

---

## 📂 Estrutura do Projeto

```
TaskFlow/
├── Taskflow/                 # Configurações Django
│   ├── settings.py          # Configurações gerais (DB, auth, idioma)
│   ├── urls.py              # Roteamento principal
│   ├── wsgi.py              # Servidor de produção
│   └── asgi.py              # Servidor async
│
├── pages/                    # Aplicação principal
│   ├── models.py            # Modelos de dados (Notebook)
│   ├── views.py             # Views (lógica das requisições)
│   ├── urls.py              # Roteamento da app
│   ├── admin.py             # Painel admin
│   ├── apps.py              # Configurações da app
│   │
│   ├── migrations/          # Migrações do banco de dados
│   │   └── 0001_initial.py
│   │
│   ├── templates/           # Templates HTML
│   │   ├── base.html        # Template base (sidebar + header)
│   │   ├── index.html       # Login
│   │   ├── recuperacao.html # Recuperação de senha
│   │   ├── cadastro.html    # Cadastro
│   │   ├── dashboard.html   # Dashboard
│   │   └── caderno.html     # Editor de notas
│   │
│   ├── static/              # Arquivos estáticos
│   │   ├── css/
│   │   │   ├── base.css         # Estilos base (sidebar, header)
│   │   │   ├── dashboard.css    # Estilos dashboard
│   │   │   └── caderno.css      # Estilos editor (modais, toasts)
│   │   │
│   │   └── js/
│   │       ├── base.js          # Lógica base (menu, header)
│   │       ├── index.js         # Lógica login
│   │       ├── cadastro.js      # Lógica cadastro
│   │       ├── dashboard.js     # Lógica dashboard
│   │       └── caderno.js       # Lógica editor (modais, toasts, save)
│   │
│   └── tests.py             # Testes unitários
│
├── db.sqlite3               # Banco de dados SQLite
├── manage.py                # CLI Django
└── readme.md                # Este arquivo
```

---

## 🚀 Como Executar

### Pré-requisitos
- Python 3.8+
- pip (gerenciador de pacotes Python)
- Ambiente virtual (recomendado)

### 1. Ativar Ambiente Virtual (Windows PowerShell)
```powershell
(Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& d:\Django\.venv\Scripts\Activate.ps1)
```

### 2. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 3. Aplicar Migrações
```bash
python manage.py migrate
```

### 4. Criar Superusuário (Opcional - para Admin)
```bash
python manage.py createsuperuser
```

### 5. Executar Servidor
```bash
python manage.py runserver
```

A aplicação estará disponível em: **http://127.0.0.1:8000**

---

## 📚 Funcionalidades Principais

### 🔐 Autenticação
- **Login** - Email e senha com validação
  - Sessão com cookie HTTP-only (2 semanas)
  - Opção "Lembrar-me" para sessão estendida
  - Redirect automático para dashboard

- **Cadastro** - Validações em tempo real
  - Nome ≥ 3 caracteres
  - Senha ≥ 8 caracteres com requisitos:
    - Pelo menos 1 letra maiúscula
    - Pelo menos 1 número
    - Pelo menos 1 caractere especial
  - Confirmação de senha
  - Aceitar termos de serviço
  
- **Recuperação de Senha** - Placeholder para implementação futura
- **Logout** - Limpeza de sessão

### 📝 Editor de Notas (Caderno)
- **Criar Notas** - Modal customizado com nome da nota
  - Criação rápida via modal
  - Entrada automática de foco

- **Editar Notas** - Editor WYSIWYG completo
  - **Formatação:**
    - ✅ Negrito (Ctrl+B)
    - ✅ Itálico (Ctrl+I)
    - ✅ Sublinhado (Ctrl+U)
    - ✅ Código (em blocos)
    - ✅ Listas (ul/ol)
    - ✅ Links (com modal customizado)
  
  - **Auto-save** - Salva automaticamente a cada 1.5s
    - Status visual: "Salvando..." → "Salvo" → "Último salvo: HH:MM"
    - Apenas salva se houver alterações
    - Aviso ao sair da página com alterações não salvas

- **Deletar Notas** - Modal de confirmação com botão vermelho
  - Confirmação obrigatória
  - Toast de sucesso
  - Redirect para lista de notas

- **Metadados**
  - Proprietário
  - Visibilidade (Privado/Público)
  - Data de criação/atualização

### 📊 Dashboard
- **Estatísticas** - Cards com métricas
- **Gráfico de Barras** - Visualização de tarefas por dia
- **Lista de Tarefas** - Itens com checkbox
- **Feed de Atividades** - Histórico de ações

### 🎨 Interface
- **Sidebar** - Navegação fixa com:
  - Logo
  - Links para Tarefas, Caderno, Teams, Análise
  - Menu de configurações e suporte
  - Ativação de estado para página atual

- **Header** - Topo com:
  - Barra de busca
  - Ícones de notificações, ajuda, configurações
  - Menu de usuário com profile/logout

- **Responsivo** - Adapta-se a diferentes telas:
  - Desktop (1440px+)
  - Tablet (768px - 1023px)
  - Mobile (até 767px)

---

## 🔧 Como As Coisas Funcionam

### 1. Fluxo de Autenticação
```
Usuário → Login (index.html)
   ↓
JavaScript valida email/senha
   ↓
Fetch POST para /
   ↓
Django IndexView recebe requisição
   ↓
authenticate(email, password) valida credenciais
   ↓
login() cria sessão com cookie
   ↓
Redirect para /dashboard/
   ↓
LoginRequiredMixin verifica sessão
   ↓
Dashboard carrega se autenticado
```

### 2. Fluxo de Salvamento de Notas
```
Usuário digita no editor
   ↓
Evento 'input' dispara debouncedSave()
   ↓
Aguarda 1.5s sem nova digitação
   ↓
saveNotebook() envia Fetch POST para /api/notebook/save/
   ↓
Django NotebookSaveAPI recebe JSON
   ↓
Verifica proprietário (ownership check)
   ↓
Salva título + conteúdo (innerHTML)
   ↓
Atualiza timestamp updated_at
   ↓
Retorna JSON success: true
   ↓
Frontend mostra "Salvo" no status
   ↓
Após 2s mostra "Último salvo: HH:MM"
```

### 3. Fluxo de Formatação de Texto
```
Usuário clica botão "Negrito"
   ↓
Mousedown event (preserva seleção)
   ↓
e.preventDefault() evita perda de foco
   ↓
document.execCommand('bold') aplica formatação
   ↓
queryCommandState() verifica se está ativo
   ↓
Botão recebe classe .active (visual feedback)
   ↓
debouncedSave() dispara auto-save
   ↓
innerHTML é salvo com tags HTML reais (<b>, <i>, <u>)
```

### 4. Fluxo de Modais Customizados
```
Usuário clica "Novo Caderno"
   ↓
showModalCreateNotebook() executa
   ↓
Modal recebe classe .active (display: flex)
   ↓
Input recebe auto-focus
   ↓
Usuário digita + pressiona Enter
   ↓
handleConfirm() valida input
   ↓
Se vazio → showToast('erro', 'error')
   ↓
Se válido → Fetch POST para /api/notebook/create/
   ↓
Django NotebookCreateAPI cria novo Notebook
   ↓
Retorna notebook.id + title
   ↓
showToast('sucesso', 'success')
   ↓
Após 500ms → window.location.href = '/caderno/{id}/'
```

---

## 🔒 Segurança

### CSRF Protection (Cross-Site Request Forgery)
- Token CSRF incluso em todos os POST via X-CSRFToken header
- getCookie('csrftoken') extrai token dos cookies
- @method_decorator(csrf_protect) em todas as views

### Session Security
- Cookies HTTP-only (não acessíveis por JavaScript)
- SESSION_COOKIE_AGE = 1209600 (2 semanas)
- Backend de sessão: django.contrib.sessions.backends.db
- LoginRequiredMixin valida acesso a páginas protegidas

### Password Security
- Argon2PasswordHasher (mais seguro que bcrypt)
- PBKDF2 e BCrypt como fallback
- Mínimo 8 caracteres + requisitos de complexidade
- Hash unidirecional (não reversível)

### Data Ownership
- Verificação de proprietário em todas as APIs
- Usuário só pode deletar/editar suas próprias notas
- QuerySet filtrado por current_user

---

## 🎯 Variáveis de Ambiente (settings.py)

```python
DEBUG = True  # Mude para False em produção
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': 'db.sqlite3'}}
INSTALLED_APPS = ['django.contrib.auth', 'django.contrib.contenttypes', 'pages', ...]
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 1209600
```

---

## 📡 Endpoints da API

| Método | URL | Descrição | Auth |
|--------|-----|-----------|------|
| GET | / | Login page | ❌ |
| POST | / | Autenticar | ❌ |
| GET | /cadastro/ | Signup page | ❌ |
| POST | /cadastro/ | Criar usuário | ❌ |
| GET | /recuperacao/ | Password recovery page | ❌ |
| GET | /logout/ | Logout | ✅ |
| GET | /dashboard/ | Dashboard | ✅ |
| GET | /caderno/ | Lista de notas | ✅ |
| GET | /caderno/{id}/ | Nota específica | ✅ |
| POST | /api/notebook/create/ | Criar nota | ✅ |
| POST | /api/notebook/save/ | Salvar nota | ✅ |
| POST | /api/notebook/delete/ | Deletar nota | ✅ |
| POST | /api/notebook/list/ | Listar notas (JSON) | ✅ |

---

## 🎨 Temas e Cores (CSS Variables)

```css
--primary-color: #0f172a      /* Azul escuro */
--accent-color: #06b6d4       /* Ciano */
--bg-white: #ffffff           /* Branco */
--bg-light: #f8fafc           /* Cinza muito claro */
--text-dark: #1e293b          /* Texto escuro */
--text-light: #64748b         /* Texto cinza */
--border-color: #e2e8f0       /* Borda cinza */
--success: #10b981            /* Verde */
--error: #ef4444              /* Vermelho */
```

---

## 📱 Responsividade

### Breakpoints
- **Desktop**: 1440px+ (layout completo com 3 colunas)
- **Tablet**: 1024px - 1023px (ajustes)
- **Mobile**: 768px - 1023px (layout ajustado)
- **Small Mobile**: até 480px (sidebar colapsada)

### Comportamentos
- Sidebar: Fixa em desktop, collapse em mobile
- Header: Adapta-se com ícones em mobile
- Editor: Fullwidth em mobile
- Toast/Modals: Respeitam viewport

---

## 🚦 Status das Features

### ✅ Completo
- Autenticação (login/cadastro/logout)
- Editor WYSIWYG com formatação
- Auto-save com debounce
- Modais customizados (criar, link, confirmar)
- Toast notifications
- Dashboard básico
- Responsividade

### 🔄 Parcial
- Recuperação de senha (UI pronta, backend não implementado)
- Visibilidade de notas (select pronto, backend não salva)
- Features do dashboard (UI pronta, lógica não implementada)

### ⏳ Futuro
- Kanban view (Tarefas)
- Gerenciamento de equipes
- Análise e relatórios
- Compartilhamento de notas
- Histórico de versões
- Busca avançada
- Tags/categorias

---

## 🐛 Troubleshooting

### Erro 404 ao acessar /dashboard/
- Certifique-se de estar autenticado
- Verifique sessão nos cookies do navegador
- Limpe cache e tente novamente

### Notas não estão salvando
- Abra o console do navegador (F12)
- Verifique se há erros de CSRF
- Confirme que o servidor está rodando

### Formatação não aparece
- Pode ser cache do navegador
- Limpe Cache → Ctrl+Shift+Delete
- Recarregue a página

### Problema com variáveis CSS
- Abra DevTools → Elements
- Procure por :root no html
- Verifique se as cores estão definidas

---

## 📖 Documentação Adicional

Para detalhes específicos sobre funcionalidades, consulte:
- **Django**: https://docs.djangoproject.com/
- **HTML5 Contenteditable**: https://developer.mozilla.org/en-US/docs/Web/Guide/HTML/Editable_content
- **Fetch API**: https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API
- **CSS Grid**: https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Grid_Layout

---

## 👨‍💻 Autor

Desenvolvido como projeto educacional em Django + Vanilla JavaScript.

---

**Última atualização**: Maio 2026