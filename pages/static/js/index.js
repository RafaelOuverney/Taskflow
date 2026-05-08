// ===== DOM Elements =====
const loginForm = document.getElementById('loginForm');
const emailInput = document.getElementById('email');
const passwordInput = document.getElementById('password');
const googleBtn = document.getElementById('googleBtn');
const githubBtn = document.getElementById('githubBtn');

function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function validatePassword(password) {
    return password.length >= 6;
}

loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const email = emailInput.value.trim();
    const password = passwordInput.value;

    if (!validateEmail(email)) {
        showError(emailInput, 'E-mail inválido');
        return;
    }

    if (!validatePassword(password)) {
        showError(passwordInput, 'A senha deve ter pelo menos 6 caracteres');
        return;
    }

    clearError(emailInput);
    clearError(passwordInput);

    const submitBtn = loginForm.querySelector('.btn-login');
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Logging in...';

    try {
        await new Promise(resolve => setTimeout(resolve, 1500));

        showSuccess('Login successful! Redirecting...');


    } catch (error) {
        showError(emailInput, 'Login failed. Please try again.');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
});

function showError(input, message) {
    input.style.borderColor = '#f87171';
    input.style.backgroundColor = 'rgba(248, 113, 113, 0.05)';

    const errorMsg = document.createElement('span');
    errorMsg.className = 'error-message';
    errorMsg.textContent = message;
    errorMsg.style.color = '#f87171';
    errorMsg.style.fontSize = '12px';
    errorMsg.style.marginTop = '-6px';

    const existing = input.parentElement.querySelector('.error-message');
    if (existing) existing.remove();

    input.parentElement.appendChild(errorMsg);
}

function clearError(input) {
    input.style.borderColor = '#e2e8f0';
    input.style.backgroundColor = '#f7fafc';
    const errorMsg = input.parentElement.querySelector('.error-message');
    if (errorMsg) errorMsg.remove();
}

function showSuccess(message) {
    const successMsg = document.createElement('div');
    successMsg.className = 'success-message';
    successMsg.innerHTML = `<i class="fas fa-check-circle"></i> ${message}`;
    successMsg.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        background-color: #10b981;
        color: white;
        border-radius: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 14px;
        font-weight: 600;
        z-index: 1000;
        animation: slideIn 0.3s ease;
    `;

    document.body.appendChild(successMsg);

    setTimeout(() => {
        successMsg.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => successMsg.remove(), 300);
    }, 3000);
}

const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

googleBtn.addEventListener('click', (e) => {
    e.preventDefault();
    handleSocialLogin('Google');
});

githubBtn.addEventListener('click', (e) => {
    e.preventDefault();
    handleSocialLogin('GitHub');
});

function handleSocialLogin(provider) {
    console.log(`${provider} login clicked`);
    showSuccess(`${provider} login initiated...`);
}
emailInput.addEventListener('blur', () => {
    if (emailInput.value.trim() && !validateEmail(emailInput.value)) {
        showError(emailInput, 'Invalid email format');
    } else {
        clearError(emailInput);
    }
});

emailInput.addEventListener('input', () => {
    if (emailInput.value.trim() && validateEmail(emailInput.value)) {
        clearError(emailInput);
    }
});

passwordInput.addEventListener('input', () => {
    clearError(passwordInput);
});

passwordInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        loginForm.dispatchEvent(new Event('submit'));
    }
});

emailInput.addEventListener('focus', () => {
    emailInput.parentElement.style.opacity = '1';
});

passwordInput.addEventListener('focus', () => {
    passwordInput.parentElement.style.opacity = '1';
});

function addPasswordToggle() {
    const passwordContainer = passwordInput.parentElement;
    const toggleBtn = document.createElement('button');
    toggleBtn.type = 'button';
    toggleBtn.className = 'password-toggle';
    toggleBtn.innerHTML = '<i class="fas fa-eye"></i>';
    toggleBtn.style.cssText = `
        position: absolute;
        right: 12px;
        top: 50%;
        transform: translateY(-50%);
        background: none;
        border: none;
        color: #64748b;
        cursor: pointer;
        font-size: 16px;
        padding: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
    `;

    toggleBtn.addEventListener('click', (e) => {
        e.preventDefault();
        const isPassword = passwordInput.type === 'password';
        passwordInput.type = isPassword ? 'text' : 'password';
        toggleBtn.innerHTML = isPassword ? '<i class="fas fa-eye-slash"></i>' : '<i class="fas fa-eye"></i>';
    });

}

console.log('Login form initialized successfully');
