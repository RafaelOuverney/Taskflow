
document.addEventListener('DOMContentLoaded', () => {
    const permBtns = document.querySelectorAll('.perm-btn');
    
    permBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            permBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
        });
    });
});