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
        console.log('Nova tarefa clicada');
        alert('Função de nova tarefa em desenvolvimento');
    });
}

const searchInput = document.querySelector('.search-bar input');
if (searchInput) {
    searchInput.addEventListener('input', (e) => {
        console.log('Busca:', e.target.value);
    });
}

console.log('Base JS initialized');
