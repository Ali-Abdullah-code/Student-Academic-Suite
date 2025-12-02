document.addEventListener('DOMContentLoaded', function () {
    const loginForm = document.getElementById('loginForm');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const emailError = document.getElementById('email-error');
    const passwordError = document.getElementById('password-error');

    if (!loginForm) return;

    loginForm.addEventListener('submit', function (event) {
        let isValid = true;

        // Reset errors
        emailError.textContent = '';
        passwordError.textContent = '';
        emailInput.classList.remove('error-border');
        passwordInput.classList.remove('error-border');

        // Email validation
        if (emailInput.value.trim() === '') {
            emailError.textContent = 'Email cannot be empty.';
            emailInput.classList.add('error-border');
            isValid = false;
        } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailInput.value)) {
            emailError.textContent = 'Please enter a valid email address.';
            emailInput.classList.add('error-border');
            isValid = false;
        }

        // Password validation
        if (passwordInput.value.trim() === '') {
            passwordError.textContent = 'Password cannot be empty.';
            passwordInput.classList.add('error-border');
            isValid = false;
        } else if (passwordInput.value.length < 6) {
            passwordError.textContent = 'Password must be at least 6 characters.';
            passwordInput.classList.add('error-border');
            isValid = false;
        }

        if (!isValid) {
            event.preventDefault();
        }
    });

    // Dynamic input feedback
    if (emailInput) {
        emailInput.addEventListener('input', function () {
            if (emailInput.value.trim() !== '' && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailInput.value)) {
                emailInput.classList.remove('error-border');
                emailError.textContent = '';
            }
        });
    }

    if (passwordInput) {
        passwordInput.addEventListener('input', function () {
            if (passwordInput.value.trim() !== '' && passwordInput.value.length >= 6) {
                passwordInput.classList.remove('error-border');
                passwordError.textContent = '';
            }
        });
    }
});