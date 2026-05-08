
const recoveryForm = document.getElementById('recoveryForm');
const emailInput = document.getElementById('email');
const successMessage = document.getElementById('successMessage');


function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}


function clearError(input) {
    input.classList.remove('error');
    const errorMsg = input.parentElement.querySelector('.error-message');
    if (errorMsg) {
        errorMsg.classList.remove('show');
    }
}


function showError(input, message) {
    input.classList.add('error');
    
    let errorMsg = input.parentElement.querySelector('.error-message');
    if (!errorMsg) {
        errorMsg = document.createElement('span');
        errorMsg.className = 'error-message';
        input.parentElement.appendChild(errorMsg);
    }
    
    errorMsg.textContent = message;
    errorMsg.classList.add('show');
}


function showSuccessMessage() {
    successMessage.classList.add('show');
    
    // Hide after 5 seconds
    setTimeout(() => {
        successMessage.classList.remove('show');
    }, 5000);
}


recoveryForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const email = emailInput.value.trim();


    if (!validateEmail(email)) {
        showError(emailInput, 'Por favor, insira um e-mail válido');
        return;
    }

    clearError(emailInput);

    const submitBtn = recoveryForm.querySelector('.btn-submit');
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enviando...';

    try {
        await new Promise(resolve => setTimeout(resolve, 1500));

        recoveryForm.style.opacity = '0';
        recoveryForm.style.pointerEvents = 'none';
        showSuccessMessage();

        recoveryForm.reset();

    } catch (error) {
        showError(emailInput, 'Erro ao enviar o link. Tente novamente.');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
});

emailInput.addEventListener('blur', () => {
    if (emailInput.value.trim() && !validateEmail(emailInput.value)) {
        showError(emailInput, 'Formato de e-mail inválido');
    } else {
        clearError(emailInput);
    }
});

emailInput.addEventListener('input', () => {
    if (emailInput.value.trim() && validateEmail(emailInput.value)) {
        clearError(emailInput);
    }
});

emailInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        recoveryForm.dispatchEvent(new Event('submit'));
    }
});

const supportLink = document.querySelector('.support-link');
if (supportLink) {
    supportLink.addEventListener('click', (e) => {
        e.preventDefault();

        recoveryForm.style.opacity = '1';
        recoveryForm.style.pointerEvents = 'auto';
        successMessage.classList.remove('show');
        recoveryForm.reset();
        emailInput.focus();
    });
}

console.log('Recovery form initialized successfully');
