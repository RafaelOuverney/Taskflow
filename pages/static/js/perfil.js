document.addEventListener('DOMContentLoaded', () => {
    const uploadBtn = document.getElementById('uploadAvatarBtn');
    const avatarInput = document.getElementById('avatarInput');
    const avatarPreview = document.getElementById('avatarPreview');

    if (uploadBtn && avatarInput) {
        uploadBtn.addEventListener('click', (e) => {
            e.preventDefault(); // Evita submeter o formulário
            avatarInput.click();
        });

        avatarInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.addEventListener('load', function() {
                    avatarPreview.setAttribute('src', this.result);
                });
                reader.readAsDataURL(file);
            }
        });
    }
});