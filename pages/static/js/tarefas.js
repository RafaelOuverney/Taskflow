const btnNewTask = document.getElementById('btnNewTask');
const btnCreateFirstTask = document.getElementById('btnCreateFirstTask');
const tasksList = document.getElementById('tasksList');
const emptyState = document.getElementById('emptyState');
const tasksSearch = document.getElementById('tasksSearch');
const filterButtons = document.querySelectorAll('.filter-btn');
const priorityButtons = document.querySelectorAll('.priority-btn');
const totalTasksSpan = document.getElementById('totalTasks');
const completedTasksSpan = document.getElementById('completedTasks');
const pendingTasksSpan = document.getElementById('pendingTasks');

let allTasks = [];
let filteredTasks = [];
let currentFilter = 'all';
let currentPriorityFilter = null;
let currentEditTaskId = null;

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

async function loadTasks() {
    try {
        const response = await fetch('/api/task/list/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();
        if (data.success) {
            allTasks = data.tasks;
            applyFilters();
            updateStats();
            renderTasks();
        }
    } catch (error) {
        console.error('Erro ao carregar tarefas:', error);
        showToast('Erro ao carregar tarefas', 'error');
    }
}

function applyFilters() {
    let filtered = allTasks;

    if (currentFilter === 'completed') {
        filtered = filtered.filter(task => task.completed);
    } else if (currentFilter === 'pending') {
        filtered = filtered.filter(task => !task.completed);
    }

    if (currentPriorityFilter) {
        filtered = filtered.filter(task => task.priority === currentPriorityFilter);
    }

    filteredTasks = filtered;
}

function updateStats() {
    const completed = allTasks.filter(t => t.completed).length;
    const pending = allTasks.filter(t => !t.completed).length;

    totalTasksSpan.textContent = allTasks.length;
    completedTasksSpan.textContent = completed;
    pendingTasksSpan.textContent = pending;
}

function renderTasks() {
    tasksList.innerHTML = '';

    if (filteredTasks.length === 0) {
        emptyState.style.display = 'flex';
        return;
    }

    emptyState.style.display = 'none';

    filteredTasks.forEach(task => {
        const taskElement = createTaskElement(task);
        tasksList.appendChild(taskElement);
    });
}

function createTaskElement(task) {
    const div = document.createElement('div');
    div.className = `task-item ${task.completed ? 'completed' : ''}`;
    div.dataset.taskId = task.id;

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.className = 'task-checkbox';
    checkbox.checked = task.completed;
    checkbox.addEventListener('change', () => toggleTask(task.id, checkbox.checked));

    const content = document.createElement('div');
    content.className = 'task-content';

    const header = document.createElement('div');
    header.className = 'task-header';

    const title = document.createElement('h3');
    title.className = 'task-title';
    title.textContent = task.title;

    const priority = document.createElement('span');
    priority.className = `task-priority ${task.priority}`;
    priority.innerHTML = `<span class="priority-dot ${task.priority}"></span> ${capitalizeFirst(task.priority)}`;

    header.appendChild(title);
    header.appendChild(priority);

    if (task.description) {
        const desc = document.createElement('p');
        desc.className = 'task-description';
        desc.textContent = task.description;
        content.appendChild(desc);
    }

    if (task.subtasks && task.subtasks.length > 0) {
        const subtasksDiv = createSubtasksElement(task);
        content.appendChild(subtasksDiv);
    }

    const actions = document.createElement('div');
    actions.className = 'task-actions';

    const btnEdit = document.createElement('button');
    btnEdit.className = 'btn-task-action';
    btnEdit.innerHTML = '<i class="fas fa-edit"></i> Editar';
    btnEdit.addEventListener('click', () => showModalEditTask(task));

    const btnDelete = document.createElement('button');
    btnDelete.className = 'btn-task-action delete';
    btnDelete.innerHTML = '<i class="fas fa-trash"></i> Deletar';
    btnDelete.addEventListener('click', () => deleteTask(task.id));

    actions.appendChild(btnEdit);
    actions.appendChild(btnDelete);

    content.appendChild(header);
    content.appendChild(actions);

    div.appendChild(checkbox);
    div.appendChild(content);

    return div;
}

function createSubtasksElement(task) {
    const div = document.createElement('div');
    div.className = 'task-subtasks';

    const header = document.createElement('div');
    header.className = 'subtasks-header';
    header.innerHTML = `Sub-tarefas (${task.subtasks_completed}/${task.subtasks_count})`;

    const list = document.createElement('div');
    list.className = 'subtasks-list';

    task.subtasks.forEach(subtask => {
        const item = document.createElement('div');
        item.className = `subtask-item ${subtask.completed ? 'completed' : ''}`;

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'subtask-checkbox';
        checkbox.checked = subtask.completed;
        checkbox.addEventListener('change', () => toggleSubtask(subtask.id, checkbox.checked));

        const title = document.createElement('span');
        title.className = 'subtask-title';
        title.textContent = subtask.title;

        const btnDelete = document.createElement('button');
        btnDelete.className = 'btn-subtask-delete';
        btnDelete.innerHTML = '<i class="fas fa-times"></i>';
        btnDelete.title = 'Deletar';
        btnDelete.addEventListener('click', () => deleteSubtask(subtask.id));

        item.appendChild(checkbox);
        item.appendChild(title);
        item.appendChild(btnDelete);
        list.appendChild(item);
    });

    const btnAdd = document.createElement('button');
    btnAdd.className = 'btn-add-subtask';
    btnAdd.innerHTML = '<i class="fas fa-plus"></i> Adicionar sub-tarefa';
    btnAdd.addEventListener('click', () => showModalAddSubtask(task.id));

    div.appendChild(header);
    div.appendChild(list);
    div.appendChild(btnAdd);

    return div;
}

function showModalCreateTask() {
    const modal = document.getElementById('modalCreateTask');
    const input = document.getElementById('inputTaskTitle');
    const btnCancel = document.getElementById('btnCancelTask');
    const btnConfirm = document.getElementById('btnConfirmTask');

    modal.classList.add('active');
    input.value = '';
    input.focus();

    const handleConfirm = async () => {
        const title = input.value.trim();
        if (!title) {
            showToast('Por favor, digite um título para a tarefa', 'error');
            return;
        }

        const priority = document.querySelector('input[name="taskPriority"]:checked').value;

        btnConfirm.disabled = true;
        btnConfirm.textContent = 'Criando...';

        try {
            const response = await fetch('/api/task/create/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ title: title, priority: priority })
            });

            const data = await response.json();
            if (data.success) {
                showToast('Tarefa criada com sucesso!', 'success');
                handleCancel();
                loadTasks();
            } else {
                showToast('Erro ao criar tarefa: ' + data.message, 'error');
                btnConfirm.disabled = false;
                btnConfirm.textContent = 'Criar Tarefa';
            }
        } catch (error) {
            console.error('Erro:', error);
            showToast('Erro ao criar tarefa', 'error');
            btnConfirm.disabled = false;
            btnConfirm.textContent = 'Criar Tarefa';
        }
    };

    const handleCancel = () => {
        modal.classList.remove('active');
        cleanup();
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter') {
            handleConfirm();
        } else if (e.key === 'Escape') {
            handleCancel();
        }
    };

    const cleanup = () => {
        btnCancel.removeEventListener('click', handleCancel);
        btnConfirm.removeEventListener('click', handleConfirm);
        input.removeEventListener('keypress', handleKeyPress);
        btnConfirm.disabled = false;
        btnConfirm.textContent = 'Criar Tarefa';
    };

    btnCancel.addEventListener('click', handleCancel);
    btnConfirm.addEventListener('click', handleConfirm);
    input.addEventListener('keypress', handleKeyPress);
}

function showModalEditTask(task) {
    currentEditTaskId = task.id;
    const modal = document.getElementById('modalEditTask');
    const inputTitle = document.getElementById('inputEditTaskTitle');
    const inputDesc = document.getElementById('inputEditTaskDesc');
    const btnCancel = document.getElementById('btnCancelEditTask');
    const btnConfirm = document.getElementById('btnConfirmEditTask');

    inputTitle.value = task.title;
    inputDesc.value = task.description;
    document.querySelector('input[name="editTaskPriority"][value="' + task.priority + '"]').checked = true;

    modal.classList.add('active');
    inputTitle.focus();

    const handleConfirm = async () => {
        const title = inputTitle.value.trim();
        if (!title) {
            showToast('Por favor, digite um título para a tarefa', 'error');
            return;
        }

        const priority = document.querySelector('input[name="editTaskPriority"]:checked').value;
        const description = inputDesc.value;

        btnConfirm.disabled = true;
        btnConfirm.textContent = 'Salvando...';

        try {
            const response = await fetch('/api/task/update/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    task_id: task.id,
                    title: title,
                    description: description,
                    priority: priority
                })
            });

            const data = await response.json();
            if (data.success) {
                showToast('Tarefa atualizada com sucesso!', 'success');
                handleCancel();
                loadTasks();
            } else {
                showToast('Erro ao atualizar tarefa: ' + data.message, 'error');
                btnConfirm.disabled = false;
                btnConfirm.textContent = 'Salvar Alterações';
            }
        } catch (error) {
            console.error('Erro:', error);
            showToast('Erro ao atualizar tarefa', 'error');
            btnConfirm.disabled = false;
            btnConfirm.textContent = 'Salvar Alterações';
        }
    };

    const handleCancel = () => {
        modal.classList.remove('active');
        cleanup();
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Escape') {
            handleCancel();
        }
    };

    const cleanup = () => {
        btnCancel.removeEventListener('click', handleCancel);
        btnConfirm.removeEventListener('click', handleConfirm);
        document.removeEventListener('keydown', handleKeyPress);
        btnConfirm.disabled = false;
        btnConfirm.textContent = 'Salvar Alterações';
    };

    btnCancel.addEventListener('click', handleCancel);
    btnConfirm.addEventListener('click', handleConfirm);
    document.addEventListener('keydown', handleKeyPress);
}

async function toggleTask(taskId, completed) {
    try {
        const response = await fetch('/api/task/toggle/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                task_id: taskId,
                completed: completed
            })
        });

        const data = await response.json();
        if (data.success) {
            loadTasks();
            const status = completed ? 'concluída' : 'marcada como pendente';
            showToast(`Tarefa ${status}!`, 'success');
        } else {
            showToast('Erro ao atualizar tarefa', 'error');
        }
    } catch (error) {
        console.error('Erro:', error);
        showToast('Erro ao atualizar tarefa', 'error');
    }
}

async function deleteTask(taskId) {
    const confirmed = await showModalConfirm(
        'Deletar Tarefa',
        'Tem certeza que deseja deletar esta tarefa? Todas as sub-tarefas também serão deletadas.',
        true
    );

    if (!confirmed) return;

    try {
        const response = await fetch('/api/task/delete/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ task_id: taskId })
        });

        const data = await response.json();
        if (data.success) {
            showToast('Tarefa deletada com sucesso!', 'success');
            loadTasks();
        } else {
            showToast('Erro ao deletar tarefa: ' + data.message, 'error');
        }
    } catch (error) {
        console.error('Erro:', error);
        showToast('Erro ao deletar tarefa', 'error');
    }
}

function showModalAddSubtask(taskId) {
    const input = prompt('Digite o título da sub-tarefa:');
    if (!input || !input.trim()) return;

    createSubtask(taskId, input.trim());
}

async function createSubtask(taskId, title) {
    try {
        const response = await fetch('/api/subtask/create/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                task_id: taskId,
                title: title
            })
        });

        const data = await response.json();
        if (data.success) {
            showToast('Sub-tarefa criada com sucesso!', 'success');
            loadTasks();
        } else {
            showToast('Erro ao criar sub-tarefa: ' + data.message, 'error');
        }
    } catch (error) {
        console.error('Erro:', error);
        showToast('Erro ao criar sub-tarefa', 'error');
    }
}

async function toggleSubtask(subtaskId, completed) {
    try {
        const response = await fetch('/api/subtask/toggle/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                subtask_id: subtaskId,
                completed: completed
            })
        });

        const data = await response.json();
        if (data.success) {
            loadTasks();
        } else {
            showToast('Erro ao atualizar sub-tarefa', 'error');
        }
    } catch (error) {
        console.error('Erro:', error);
        showToast('Erro ao atualizar sub-tarefa', 'error');
    }
}

async function deleteSubtask(subtaskId) {
    try {
        const response = await fetch('/api/subtask/delete/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ subtask_id: subtaskId })
        });

        const data = await response.json();
        if (data.success) {
            showToast('Sub-tarefa deletada com sucesso!', 'success');
            loadTasks();
        } else {
            showToast('Erro ao deletar sub-tarefa', 'error');
        }
    } catch (error) {
        console.error('Erro:', error);
        showToast('Erro ao deletar sub-tarefa', 'error');
    }
}

function showModalConfirm(title, message, isDangerous = false) {
    return new Promise((resolve) => {
        const modal = document.getElementById('modalConfirm');
        const modalTitle = document.getElementById('confirmTitle');
        const modalMessage = document.getElementById('confirmMessage');
        const btnCancel = document.getElementById('btnConfirmCancel');
        const btnOk = document.getElementById('btnConfirmOk');

        modalTitle.textContent = title;
        modalMessage.textContent = message;

        if (isDangerous) {
            btnOk.className = 'modal-btn modal-btn-danger';
            btnOk.textContent = 'Deletar';
        } else {
            btnOk.className = 'modal-btn modal-btn-primary';
            btnOk.textContent = 'Confirmar';
        }

        modal.classList.add('active');
        btnOk.focus();

        const handleConfirm = () => {
            modal.classList.remove('active');
            cleanup();
            resolve(true);
        };

        const handleCancel = () => {
            modal.classList.remove('active');
            cleanup();
            resolve(false);
        };

        const handleKeyPress = (e) => {
            if (e.key === 'Enter') {
                handleConfirm();
            } else if (e.key === 'Escape') {
                handleCancel();
            }
        };

        const cleanup = () => {
            btnCancel.removeEventListener('click', handleCancel);
            btnOk.removeEventListener('click', handleConfirm);
            document.removeEventListener('keydown', handleKeyPress);
        };

        btnCancel.addEventListener('click', handleCancel);
        btnOk.addEventListener('click', handleConfirm);
        document.addEventListener('keydown', handleKeyPress);
    });
}

function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toastContainer');

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    let icon = 'fa-info-circle';
    if (type === 'success') icon = 'fa-check-circle';
    else if (type === 'error') icon = 'fa-exclamation-circle';

    toast.innerHTML = `
        <i class="fas ${icon} toast-icon"></i>
        <span class="toast-message">${message}</span>
        <button class="toast-close" title="Fechar">
            <i class="fas fa-times"></i>
        </button>
    `;

    container.appendChild(toast);

    const closeBtn = toast.querySelector('.toast-close');
    const removeToast = () => {
        toast.classList.add('removing');
        setTimeout(() => {
            toast.remove();
        }, 300);
    };

    closeBtn.addEventListener('click', removeToast);

    if (duration > 0) {
        setTimeout(removeToast, duration);
    }

    return toast;
}

tasksSearch.addEventListener('input', (e) => {
    const searchTerm = e.target.value.toLowerCase();
    filteredTasks = allTasks.filter(task =>
        task.title.toLowerCase().includes(searchTerm) ||
        task.description.toLowerCase().includes(searchTerm)
    );

    if (currentFilter === 'completed') {
        filteredTasks = filteredTasks.filter(task => task.completed);
    } else if (currentFilter === 'pending') {
        filteredTasks = filteredTasks.filter(task => !task.completed);
    }

    if (currentPriorityFilter) {
        filteredTasks = filteredTasks.filter(task => task.priority === currentPriorityFilter);
    }

    renderTasks();
});

filterButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        filterButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentFilter = btn.dataset.filter;
        applyFilters();
        renderTasks();
    });
});

priorityButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        const priority = btn.dataset.priority;
        if (currentPriorityFilter === priority) {
            currentPriorityFilter = null;
            btn.style.opacity = '1';
        } else {
            priorityButtons.forEach(b => b.style.opacity = '0.5');
            btn.style.opacity = '1';
            currentPriorityFilter = priority;
        }
        applyFilters();
        renderTasks();
    });
});

btnNewTask.addEventListener('click', showModalCreateTask);
btnCreateFirstTask.addEventListener('click', showModalCreateTask);

function capitalizeFirst(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

loadTasks();
