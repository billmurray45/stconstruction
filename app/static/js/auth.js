// Auth API Module
const AuthAPI = {
    // Регистрация пользователя
    async register(formData) {
        try {
            const response = await fetchWithCsrf('/auth/register', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Registration error:', error);
            return { success: false, message: 'Ошибка соединения с сервером' };
        }
    },

    // Авторизация пользователя
    async login(formData) {
        try {
            const response = await fetchWithCsrf('/auth/login', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Login error:', error);
            return { success: false, message: 'Ошибка соединения с сервером' };
        }
    },

    // Выход из системы
    async logout() {
        try {
            const response = await fetchWithCsrf('/auth/logout', {
                method: 'POST'
            });

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Logout error:', error);
            return { success: false, message: 'Ошибка соединения с сервером' };
        }
    },

    // Получить текущего пользователя
    async getCurrentUser() {
        try {
            const response = await fetch('/auth/me', {
                method: 'GET'
            });

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Get user error:', error);
            return { success: false, message: 'Ошибка соединения с сервером' };
        }
    }
};

// Modal Manager
const ModalManager = {
    modal: null,
    loginFormContainer: null,
    registerFormContainer: null,

    init() {
        this.modal = document.getElementById('authModal');

        if (!this.modal) {
            console.log('Auth modal not found - user is authenticated');
            return;
        }

        this.loginFormContainer = document.getElementById('loginForm');
        this.registerFormContainer = document.getElementById('registerForm');

        const loginButton = document.getElementById('loginButton');
        if (loginButton) {
            loginButton.addEventListener('click', () => this.open('login'));
        }

        const closeButton = document.getElementById('closeAuthModal');
        if (closeButton) {
            closeButton.addEventListener('click', () => this.close());
        }

        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.close();
            }
        });

        document.querySelectorAll('.auth-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const tabName = e.target.dataset.tab;
                this.switchTab(tabName);
            });
        });
    },

    open(tab = 'login') {
        this.modal.classList.add('active');
        this.switchTab(tab);
        document.body.style.overflow = 'hidden';
    },

    close() {
        this.modal.classList.remove('active');
        document.body.style.overflow = '';
        this.clearErrors();
    },

    switchTab(tabName) {
        // Переключить активную вкладку
        document.querySelectorAll('.auth-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Переключить форму
        this.loginFormContainer.classList.remove('active');
        this.registerFormContainer.classList.remove('active');

        if (tabName === 'login') {
            this.loginFormContainer.classList.add('active');
        } else {
            this.registerFormContainer.classList.add('active');
        }

        this.clearErrors();
    },

    showError(formType, message) {
        const errorElement = document.getElementById(`${formType}Error`);
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.classList.add('active');
        }
    },

    clearErrors() {
        document.querySelectorAll('.form-error').forEach(error => {
            error.textContent = '';
            error.classList.remove('active');
        });
    }
};

// Profile Modal Manager
const ProfileModalManager = {
    modal: null,
    profileButton: null,
    closeButton: null,

    init() {
        this.modal = document.getElementById('profileModal');

        if (!this.modal) {
            console.log('Profile modal not found - user is not authenticated');
            return;
        }

        this.profileButton = document.getElementById('profileButton');
        this.closeButton = document.getElementById('closeProfileModal');
        const logoutButton = document.getElementById('logoutButton');

        if (this.profileButton) {
            this.profileButton.addEventListener('click', () => {
                this.open();
            });
        }

        if (this.closeButton) {
            this.closeButton.addEventListener('click', () => {
                this.close();
            });
        }

        if (this.modal) {
            this.modal.addEventListener('click', (e) => {
                if (e.target === this.modal) {
                    this.close();
                }
            });
        }

        // Выход из системы
        if (logoutButton) {
            logoutButton.addEventListener('click', async (e) => {
                e.preventDefault();

                const result = await AuthAPI.logout();

                if (result.success) {
                    window.location.reload();
                } else {
                    alert(result.message || 'Ошибка при выходе из системы');
                }
            });
        }
    },

    async open() {
        this.modal.classList.add('active');
        document.body.style.overflow = 'hidden';

        // Загружаем данные пользователя
        await this.loadUserData();
    },

    close() {
        this.modal.classList.remove('active');
        document.body.style.overflow = '';
    },

    async loadUserData() {
        const profileContent = document.getElementById('profileContent');
        const profileData = document.getElementById('profileData');

        profileContent.style.display = 'block';
        profileData.style.display = 'none';

        const result = await AuthAPI.getCurrentUser();

        if (result.success && result.user) {
            const user = result.user;

            document.getElementById('profileEmail').textContent = user.email;
            document.getElementById('profileUsername').textContent = user.username;
            document.getElementById('profileFullName').textContent = user.full_name || 'Не указано';

            const createdDate = new Date(user.created_at);
            document.getElementById('profileCreatedAt').textContent = createdDate.toLocaleDateString('ru-RU');

            const statusSpan = document.getElementById('profileStatus');
            statusSpan.textContent = user.is_active ? 'Активен' : 'Неактивен';
            statusSpan.style.color = user.is_active ? '#28a745' : '#dc3545';

            const adminButton = document.getElementById('adminPanelButton');
            if (user.is_superuser) {
                adminButton.style.display = 'inline-block';
            } else {
                adminButton.style.display = 'none';
            }

            profileContent.style.display = 'none';
            profileData.style.display = 'block';
        } else {
            profileContent.innerHTML = '<div class="profile-loading" style="color: #dc3545;">Ошибка загрузки данных</div>';
        }
    }
};

// Form Handlers
const FormHandlers = {
    init() {
        const loginForm = document.getElementById('loginFormElement');
        const registerForm = document.getElementById('registerFormElement');

        if (!loginForm && !registerForm) {
            console.log('Auth forms not found - user is authenticated');
            return;
        }

        if (loginForm) {
            loginForm.addEventListener('submit', async (e) => {
                e.preventDefault();

                const formData = new FormData(loginForm);
                const result = await AuthAPI.login(formData);

                if (result.success) {
                    ModalManager.close();
                    window.location.reload();
                } else {
                    ModalManager.showError('login', result.message || 'Ошибка при входе');
                }
            });
        }

        if (registerForm) {
            registerForm.addEventListener('submit', async (e) => {
                e.preventDefault();

                const formData = new FormData(registerForm);
                const result = await AuthAPI.register(formData);

                if (result.success) {
                    alert(result.message || 'Регистрация успешна!');
                    ModalManager.switchTab('login');
                    registerForm.reset();

                    const email = formData.get('email');
                    document.getElementById('loginEmail').value = email;
                } else {
                    ModalManager.showError('register', result.message || 'Ошибка при регистрации');
                }
            });
        }
    }
};

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    const authModal = document.getElementById('authModal');
    const profileModal = document.getElementById('profileModal');

    if (authModal) {
        ModalManager.init();
        FormHandlers.init();
    }

    if (profileModal) {
        ProfileModalManager.init();
    }
});
