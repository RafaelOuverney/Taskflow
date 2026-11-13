const userMenuBtn = document.getElementById('userMenuBtn');
const userMenu = document.getElementById('userMenu');

userMenuBtn.addEventListener('click', () => {
    userMenu.classList.toggle('active');
});

document.addEventListener('click', (e) => {
    if (!userMenuBtn.contains(e.target) && !userMenu.contains(e.target)) {
        userMenu.classList.remove('active');
    }
});

const newTaskBtn = document.getElementById('newTaskBtn');
if (newTaskBtn) {
    newTaskBtn.addEventListener('click', () => {
        if (typeof showModalCreateTask === 'function') {
            showModalCreateTask();
        } else {
            window.location.href = '/tarefas/?new=1';
        }
    });
}

const searchInput = document.querySelector('.search-bar input');
if (searchInput) {
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            const term = searchInput.value.trim();
            window.location.href = term ? `/tarefas/?title=${encodeURIComponent(term)}` : '/tarefas/';
        }
    });
}

console.log('Base JS initialized');
