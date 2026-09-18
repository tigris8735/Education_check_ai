import { html, mount } from '../ui/render.js';
import { readForm } from '../ui/form.js';
import { toast } from '../ui/toast.js';
import { register } from '../core/auth.js';
import { navigate } from '../core/router.js';

export function renderRegister() {
  mount(html`
    <div class="auth">
      <div class="auth__card">
        <div class="auth__brand">
          <div class="topbar__logo">E</div>
          <span>EduCheck AI</span>
        </div>
        <h1 class="auth__title">Регистрация</h1>
        <p class="auth__subtitle">Создайте аккаунт преподавателя или студента</p>

        <form class="auth__form" id="reg-form" novalidate>
          <div class="field">
            <label class="field__label" for="full_name">Полное имя</label>
            <input class="input" type="text" id="full_name" name="full_name" required placeholder="Иван Иванов" />
          </div>
          <div class="field">
            <label class="field__label" for="email">Email</label>
            <input class="input" type="email" id="email" name="email" required placeholder="you@example.com" />
          </div>
          <div class="field">
            <label class="field__label" for="password">Пароль</label>
            <input class="input" type="password" id="password" name="password" required minlength="6" placeholder="Минимум 6 символов" />
          </div>
          <div class="field">
            <label class="field__label" for="role">Роль</label>
            <select class="select" id="role" name="role" required>
              <option value="STUDENT">Студент</option>
              <option value="TEACHER">Преподаватель</option>
            </select>
          </div>
          <button class="btn btn--primary btn--lg btn--block" type="submit" id="submit-btn">Создать аккаунт</button>
        </form>

        <div class="auth__footer">
          Уже есть аккаунт? <a href="#/login">Войти</a>
        </div>
      </div>
    </div>
  `);

  const form = document.getElementById('reg-form');
  const btn = document.getElementById('submit-btn');

  form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const payload = readForm(form);
  
  // Разбиваем full_name на first_name и last_name
  const fullName = payload.full_name || '';
  const nameParts = fullName.trim().split(/\s+/);
  const firstName = nameParts[0] || '';
  const lastName = nameParts.slice(1).join(' ') || '';
  
  const registerData = {
    first_name: firstName,
    last_name: lastName,
    email: payload.email,
    password: payload.password,
    role: payload.role,
  };
  
  btn.disabled = true;
  btn.textContent = 'Создание…';
  try {
    await register(registerData);
    toast('Аккаунт создан. Выполняется вход…', 'success');
    await login(payload.email, payload.password).catch(() => {});
    navigate('/');
  } catch (err) {
    toast(err.message || 'Ошибка регистрации', 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Создать аккаунт';
  }
});
}

// локальный импорт, чтобы не плодить зависимости
import { login } from '../core/auth.js';