const taskCheckboxes = document.querySelectorAll('.task-checkbox input');

taskCheckboxes.forEach(checkbox => {
    checkbox.addEventListener('change', (e) => {
        const taskItem = e.target.closest('.task-item');
        if (e.target.checked) {
            taskItem.style.opacity = '0.6';
            const taskTitle = taskItem.querySelector('.task-title').textContent;
            console.log('Tarefa concluída:', taskTitle);
        } else {
            taskItem.style.opacity = '1';
        }
    });
});

const filterBtns = document.querySelectorAll('.filter-btn');

filterBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
        filterBtns.forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
        
        const filterType = e.target.textContent.trim();
        console.log('Filtro aplicado:', filterType);
        
    });
});
const bars = document.querySelectorAll('.bar');

bars.forEach((bar, index) => {
    const days = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo'];
    const completedTasks = [45, 52, 48, 62, 55, 38, 35];
    
    bar.addEventListener('mouseenter', () => {
        const tooltip = document.createElement('div');
        tooltip.style.cssText = `
            position: absolute;
            background-color: #1a202c;
            color: white;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            white-space: nowrap;
            pointer-events: none;
            z-index: 10;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            margin-bottom: 8px;
        `;
        tooltip.textContent = `${days[index]}: ${completedTasks[index]} tarefas`;
        
        bar.parentElement.style.position = 'relative';
        bar.parentElement.appendChild(tooltip);
        
        setTimeout(() => {
            tooltip.remove();
        }, 2000);
    });
});

const taskItems = document.querySelectorAll('.task-item');

taskItems.forEach(item => {
    item.addEventListener('click', (e) => {
        if (e.target.closest('.task-checkbox')) return;
        
        const taskCode = item.querySelector('.task-code').textContent;
        const taskTitle = item.querySelector('.task-title').textContent;
        console.log('Tarefa clicada:', taskCode, '-', taskTitle);
        
    });
});

const activityItems = document.querySelectorAll('.activity-item');

activityItems.forEach(item => {
    item.addEventListener('click', () => {
        console.log('Atividade clicada');
    });
});

const viewAllLink = document.querySelector('.view-all');
if (viewAllLink) {
    viewAllLink.addEventListener('click', (e) => {
        e.preventDefault();
        console.log('Ver todas as tarefas');
    });
}

const menuBtn = document.querySelector('.menu-btn');
if (menuBtn) {
    menuBtn.addEventListener('click', () => {
        console.log('Menu de opções clicado');
    });
}

const badge = document.querySelector('.badge');
if (badge) {
    setInterval(() => {
        badge.style.animation = 'pulse 2s ease-in-out infinite';
    }, 5000);
}

const style = document.createElement('style');
style.textContent = `
    @keyframes pulse {
        0%, 100% {
            transform: scale(1);
        }
        50% {
            transform: scale(1.2);
        }
    }

    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .task-item {
        animation: slideIn 0.3s ease;
    }

    .stat-card {
        animation: slideIn 0.3s ease;
    }
`;
document.head.appendChild(style);

function updateStats() {
    console.log('Atualizando estatísticas...');
}

setInterval(updateStats, 30000);

document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('.search-bar input');
        if (searchInput) {
            searchInput.focus();
        }
    }
});

console.log('Dashboard JS initialized');
