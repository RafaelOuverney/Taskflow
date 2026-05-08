const signupForm = document.getElementById('signupForm');
const fullNameInput = document.getElementById('fullName');
const emailInput = document.getElementById('email');
const passwordInput = document.getElementById('password');
const confirmPasswordInput = document.getElementById('confirmPassword');
const termsCheckbox = document.getElementById('terms');
const togglePasswordBtn = document.getElementById('togglePassword');
const toggleConfirmPasswordBtn = document.getElementById('toggleConfirmPassword');
const googleBtn = document.getElementById('googleBtn');
const githubBtn = document.getElementById('githubBtn');

const requirements = {
    length: document.getElementById('req-length'),
    uppercase: document.getElementById('req-uppercase'),
    number: document.getElementById('req-number'),
    special: document.getElementById('req-special')
};

const passwordCriteria = {
    length: (password) => password.length >= 8,
    uppercase: (password) => /[A-Z]/.test(password),
    number: (password) => /[0-9]/.test(password),
    special: (password) => /[!@#$%^&*()_+\-=\[\]{};:'",.<>?\\\/]/.test(password)
};

function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function validateFullName(name) {
    return name.trim().length >= 3;
}

function updatePasswordRequirements(password) {
    Object.keys(passwordCriteria).forEach(criterion => {
        const isMet = passwordCriteria[criterion](password);
        const element = requirements[criterion];
        
        if (isMet) {
            element.classList.add('met');
        } else {
            element.classList.remove('met');
        }
    });
}

function isPasswordValid(password) {
    return Object.values(passwordCriteria).every(criterion => criterion(password));
}

function doPasswordsMatch() {
    if (!confirmPasswordInput.value) return false;
    return passwordInput.value === confirmPasswordInput.value;
}

function clearError(input) {
    input.classList.remove('error');
    input.classList.remove('success');
    const errorMsg = input.parentElement.querySelector('.error-message');
    if (errorMsg) {
        errorMsg.classList.remove('show');
    }
}

function showError(input, message) {
    input.classList.add('error');
    input.classList.remove('success');
    
    let errorMsg = input.parentElement.querySelector('.error-message');
    if (!errorMsg) {
        errorMsg = document.createElement('span');
        errorMsg.className = 'error-message';
        input.parentElement.appendChild(errorMsg);
    }
    
    errorMsg.textContent = message;
    errorMsg.classList.add('show');
}

function showSuccess(input) {
    input.classList.add('success');
    input.classList.remove('error');
    const errorMsg = input.parentElement.querySelector('.error-message');
    if (errorMsg) {
        errorMsg.classList.remove('show');
    }
}

function showSuccessPopup(message) {
    const popup = document.createElement('div');
    popup.className = 'success-message-popup';
    popup.innerHTML = `<i class="fas fa-check-circle"></i> ${message}`;
    document.body.appendChild(popup);

    setTimeout(() => {
        popup.classList.add('hide');
        setTimeout(() => popup.remove(), 300);
    }, 3000);
}

togglePasswordBtn.addEventListener('click', (e) => {
    e.preventDefault();
    const isPassword = passwordInput.type === 'password';
    passwordInput.type = isPassword ? 'text' : 'password';
    togglePasswordBtn.innerHTML = isPassword ? '<i class="fas fa-eye-slash"></i>' : '<i class="fas fa-eye"></i>';
});

toggleConfirmPasswordBtn.addEventListener('click', (e) => {
    e.preventDefault();
    const isPassword = confirmPasswordInput.type === 'password';
    confirmPasswordInput.type = isPassword ? 'text' : 'password';
    toggleConfirmPasswordBtn.innerHTML = isPassword ? '<i class="fas fa-eye-slash"></i>' : '<i class="fas fa-eye"></i>';
});

passwordInput.addEventListener('input', () => {
    const password = passwordInput.value;
    
    updatePasswordRequirements(password);
    
    if (password) {
        if (isPasswordValid(password)) {
            showSuccess(passwordInput);
        } else {
            clearError(passwordInput);
        }
    } else {
        clearError(passwordInput);
    }
    
    if (confirmPasswordInput.value) {
        if (doPasswordsMatch()) {
            showSuccess(confirmPasswordInput);
        } else {
            clearError(confirmPasswordInput);
        }
    }
});

confirmPasswordInput.addEventListener('input', () => {
    if (confirmPasswordInput.value) {
        if (doPasswordsMatch()) {
            showSuccess(confirmPasswordInput);
        } else {
            clearError(confirmPasswordInput);
        }
    } else {
        clearError(confirmPasswordInput);
    }
});

fullNameInput.addEventListener('blur', () => {
    if (fullNameInput.value.trim()) {
        if (validateFullName(fullNameInput.value)) {
            showSuccess(fullNameInput);
        } else {
            showError(fullNameInput, 'Nome deve ter pelo menos 3 caracteres');
        }
    }
});

fullNameInput.addEventListener('input', () => {
    if (fullNameInput.value.trim() && validateFullName(fullNameInput.value)) {
        showSuccess(fullNameInput);
    }
});

emailInput.addEventListener('blur', () => {
    if (emailInput.value.trim()) {
        if (validateEmail(emailInput.value)) {
            showSuccess(emailInput);
        } else {
            showError(emailInput, 'E-mail inválido');
        }
    }
});

emailInput.addEventListener('input', () => {
    if (emailInput.value.trim() && validateEmail(emailInput.value)) {
        showSuccess(emailInput);
    }
});

signupForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const fullName = fullNameInput.value.trim();
    const email = emailInput.value.trim();
    const password = passwordInput.value;
    const confirmPassword = confirmPasswordInput.value;
    const termsAccepted = termsCheckbox.checked;

    let isValid = true;

    if (!validateFullName(fullName)) {
        showError(fullNameInput, 'Nome deve ter pelo menos 3 caracteres');
        isValid = false;
    } else {
        showSuccess(fullNameInput);
    }

    if (!validateEmail(email)) {
        showError(emailInput, 'E-mail inválido');
        isValid = false;
    } else {
        showSuccess(emailInput);
    }

    if (!isPasswordValid(password)) {
        showError(passwordInput, 'Senha não atende aos requisitos');
        isValid = false;
    } else {
        showSuccess(passwordInput);
    }

    if (!doPasswordsMatch()) {
        showError(confirmPasswordInput, 'As senhas não coincidem');
        isValid = false;
    } else {
        showSuccess(confirmPasswordInput);
    }

    if (!termsAccepted) {
        showError(termsCheckbox, 'Você deve aceitar os termos');
        isValid = false;
    }

    if (!isValid) return;

    const submitBtn = signupForm.querySelector('.btn-create');
    const originalText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Criando conta...';

    try {
        await new Promise(resolve => setTimeout(resolve, 1500));

        showSuccessPopup('Conta criada com sucesso!');

        signupForm.reset();
        clearError(fullNameInput);
        clearError(emailInput);
        clearError(passwordInput);
        clearError(confirmPasswordInput);

        Object.values(requirements).forEach(req => req.classList.remove('met'));

        setTimeout(() => {
            window.location.href = '/';
        }, 2000);

    } catch (error) {
        showError(emailInput, 'Erro ao criar conta. Tente novamente.');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
    }
});

googleBtn.addEventListener('click', (e) => {
    e.preventDefault();
    console.log('Google signup clicked');
    showSuccessPopup('Inscrição com Google iniciada...');
});

githubBtn.addEventListener('click', (e) => {
    e.preventDefault();
    console.log('GitHub signup clicked');
    showSuccessPopup('Inscrição com GitHub iniciada...');
});

console.log('Signup form initialized successfully');
