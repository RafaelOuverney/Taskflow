// Calendar state
let currentDate = new Date();
let selectedDate = null;
let tasks = [];
let taskModal = null;

// Initialize calendar
document.addEventListener('DOMContentLoaded', () => {
    try {
        taskModal = new bootstrap.Modal(document.getElementById('taskModalCalendar'));
    } catch (e) {
        console.warn('Bootstrap modal não disponível:', e);
    }
    
    // Setup event listeners
    const prevMonthBtn = document.getElementById('prevMonth');
    const nextMonthBtn = document.getElementById('nextMonth');
    const todayBtn = document.getElementById('todayBtn');
    const btnNewTaskCalendar = document.getElementById('btnNewTaskCalendar');
    const saveTaskBtn = document.getElementById('saveTaskBtn');
    
    if (prevMonthBtn) prevMonthBtn.addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() - 1);
        renderCalendar();
    });
    
    if (nextMonthBtn) nextMonthBtn.addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() + 1);
        renderCalendar();
    });
    
    if (todayBtn) todayBtn.addEventListener('click', () => {
        currentDate = new Date();
        renderCalendar();
    });
    
    if (btnNewTaskCalendar) btnNewTaskCalendar.addEventListener('click', () => {
        resetTaskForm();
        document.getElementById('taskModalLabel').textContent = 'Nova Tarefa';
        if (selectedDate) {
            const dateStr = selectedDate.toISOString().slice(0, 16);
            document.getElementById('taskDueDate').value = dateStr;
        }
        if (taskModal) taskModal.show();
    });
    
    if (saveTaskBtn) saveTaskBtn.addEventListener('click', saveTask);
    
    // Renderizar o calendário primeiro
    renderCalendar();
    
    // Selecionar hoje
    selectedDate = new Date();
    updateSelectedDateTasks();
    
    // Depois carregar tarefas
    loadTasks();
});

// Load tasks from API
function loadTasks() {
    fetch('{% url "task_list_api" %}')
        .then(response => response.json())
        .then(data => {
            tasks = data.tasks || [];
            renderCalendar();
            renderUpcoming();
            if (selectedDate) {
                updateSelectedDateTasks();
            }
        })
        .catch(error => {
            console.error('Erro ao carregar tarefas:', error);
            // Mesmo com erro, atualiza a exibição
            updateSelectedDateTasks();
        });
}

// Render calendar
function renderCalendar() {
    const calendarDays = document.getElementById('calendarDays');
    const currentMonthYear = document.getElementById('currentMonthYear');
    
    // Verificar se o elemento existe
    if (!calendarDays) {
        console.error('Elemento calendarDays não encontrado');
        return;
    }

    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();

    // Update month/year display
    if (currentMonthYear) {
        const monthNames = [
            'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
        ];
        currentMonthYear.textContent = `${monthNames[month]} ${year}`;
    }

    // Get first day of month and number of days
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const daysInPrevMonth = new Date(year, month, 0).getDate();

    // Clear calendar
    calendarDays.innerHTML = '';

    // Previous month days
    for (let i = firstDay - 1; i >= 0; i--) {
        const day = daysInPrevMonth - i;
        const date = new Date(year, month - 1, day);
        createDayElement(date, true);
    }

    // Current month days
    for (let day = 1; day <= daysInMonth; day++) {
        const date = new Date(year, month, day);
        createDayElement(date, false);
    }

    // Next month days
    const totalCells = calendarDays.children.length;
    const remainingCells = 42 - totalCells; // 6 rows × 7 days
    for (let day = 1; day <= remainingCells; day++) {
        const date = new Date(year, month + 1, day);
        createDayElement(date, true);
    }
}

// Create day element
function createDayElement(date, isOtherMonth) {
    const dayElement = document.createElement('div');
    dayElement.className = 'calendar-day';

    if (isOtherMonth) {
        dayElement.classList.add('other-month');
    }

    // Check if today
    const today = new Date();
    if (date.toDateString() === today.toDateString()) {
        dayElement.classList.add('today');
    }

    // Check if selected
    if (selectedDate && date.toDateString() === selectedDate.toDateString()) {
        dayElement.classList.add('selected');
    }

    // Add day number
    const dayNumber = document.createElement('div');
    dayNumber.className = 'day-number';
    dayNumber.textContent = date.getDate();
    dayElement.appendChild(dayNumber);

    // Add tasks for this day
    const dayTasks = getTasksForDate(date);
    if (dayTasks.length > 0) {
        const tasksDiv = document.createElement('div');
        tasksDiv.className = 'day-tasks';

        // Show up to 2 tasks
        dayTasks.slice(0, 2).forEach(task => {
            const taskItem = document.createElement('div');
            taskItem.className = 'day-task-item';
            
            const priorityClass = task.priority === 'high' ? 'high' : 
                                 task.priority === 'medium' ? 'medium' : 'low';
            const indicator = document.createElement('span');
            indicator.className = `task-indicator ${priorityClass}`;
            
            taskItem.appendChild(indicator);
            taskItem.appendChild(document.createTextNode(task.title.substring(0, 15)));
            tasksDiv.appendChild(taskItem);
        });

        // Show count if more than 2
        if (dayTasks.length > 2) {
            const countDiv = document.createElement('div');
            countDiv.className = 'day-task-count';
            countDiv.textContent = `+${dayTasks.length - 2} mais`;
            tasksDiv.appendChild(countDiv);
        }

        dayElement.appendChild(tasksDiv);
    }

    // Click handler
    dayElement.addEventListener('click', () => {
        if (!isOtherMonth) {
            selectDate(date);
        }
    });

    calendarDays.appendChild(dayElement);
}

// Get tasks for a specific date
function getTasksForDate(date) {
    return tasks.filter(task => {
        if (!task.due_date) return false;
        const taskDate = new Date(task.due_date);
        return taskDate.toDateString() === date.toDateString();
    });
}

// Select date
function selectDate(date) {
    selectedDate = new Date(date);
    renderCalendar();
    updateSelectedDateTasks();
}

// Update selected date tasks display
function updateSelectedDateTasks() {
    const selectedDateText = document.getElementById('selectedDateText');
    const tasksListCalendar = document.getElementById('tasksListCalendar');
    
    if (!selectedDateText || !tasksListCalendar) {
        console.error('Elementos não encontrados');
        return;
    }
    
    if (!selectedDate) {
        tasksListCalendar.innerHTML = '<p class="empty-message">Selecione um dia para ver as tarefas</p>';
        selectedDateText.textContent = '-';
        return;
    }

    // Update date text
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    selectedDateText.textContent = selectedDate.toLocaleDateString('pt-BR', options);

    // Get tasks for selected date
    const dayTasks = getTasksForDate(selectedDate);

    // Update tasks list
    if (dayTasks.length === 0) {
        tasksListCalendar.innerHTML = '<p class="empty-message">Nenhuma tarefa neste dia</p>';
    } else {
        tasksListCalendar.innerHTML = '';
        dayTasks.forEach(task => {
            const taskItem = document.createElement('div');
            taskItem.className = `task-item-calendar ${task.priority}-priority`;
            if (task.completed) taskItem.classList.add('completed');

            const title = document.createElement('div');
            title.className = 'task-item-title';
            title.textContent = task.title;

            const time = document.createElement('div');
            time.className = 'task-item-time';
            const taskDate = new Date(task.due_date);
            time.textContent = taskDate.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });

            taskItem.appendChild(title);
            taskItem.appendChild(time);

            // Toggle task
            taskItem.addEventListener('click', () => {
                toggleTask(task.id);
            });

            tasksListCalendar.appendChild(taskItem);
        });
    }
}

// Render upcoming tasks
function renderUpcoming() {
    const upcomingList = document.getElementById('upcomingList');
    
    if (!upcomingList) {
        console.error('Elemento upcomingList não encontrado');
        return;
    }
    
    upcomingList.innerHTML = '';
    
    // Get tasks for next 7 days
    const upcoming = [];
    for (let i = 0; i < 7; i++) {
        const date = new Date();
        date.setDate(date.getDate() + i);
        const dayTasks = getTasksForDate(date).filter(t => !t.completed);
        upcoming.push(...dayTasks);
    }

    if (upcoming.length === 0) {
        upcomingList.innerHTML = '<p class="empty-message">Nenhuma tarefa próxima</p>';
        return;
    }

    // Sort by due date
    upcoming.sort((a, b) => new Date(a.due_date) - new Date(b.due_date));

    // Display up to 5
    upcoming.slice(0, 5).forEach(task => {
        const item = document.createElement('div');
        item.className = 'upcoming-item';

        const date = document.createElement('div');
        date.className = 'upcoming-date';
        const taskDate = new Date(task.due_date);
        date.textContent = taskDate.toLocaleDateString('pt-BR', { month: 'short', day: 'numeric' });

        const title = document.createElement('p');
        title.className = 'upcoming-title';
        title.textContent = task.title;

        item.appendChild(date);
        item.appendChild(title);
        upcomingList.appendChild(item);
    });
}

// Reset task form
function resetTaskForm() {
    const taskFormCalendar = document.getElementById('taskFormCalendar');
    const taskPriority = document.getElementById('taskPriority');
    
    if (taskFormCalendar) taskFormCalendar.reset();
    if (taskPriority) taskPriority.value = 'medium';
}

// Save task
function saveTask() {
    const taskTitle = document.getElementById('taskTitle');
    const taskDescription = document.getElementById('taskDescription');
    const taskPriority = document.getElementById('taskPriority');
    const taskDueDate = document.getElementById('taskDueDate');
    
    if (!taskTitle || !taskTitle.value.trim()) {
        alert('Por favor, insira um título');
        return;
    }

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                     getCookie('csrftoken');

    const data = {
        title: taskTitle.value.trim(),
        description: taskDescription.value.trim(),
        priority: taskPriority.value,
        due_date: new Date(taskDueDate.value).toISOString()
    };

    fetch('{% url "task_create_api" %}', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (taskModal) taskModal.hide();
            loadTasks();
        } else {
            alert('Erro ao salvar tarefa: ' + (data.message || 'Tente novamente'));
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        alert('Erro ao salvar tarefa');
    });
}

// Toggle task completion
function toggleTask(taskId) {
    const csrfToken = getCookie('csrftoken');

    fetch('{% url "task_toggle_api" %}', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ task_id: taskId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadTasks();
        }
    })
    .catch(error => console.error('Erro:', error));
}

// Utility function to get CSRF token
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
