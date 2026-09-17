import { html, mount } from '../ui/render.js';
import { readForm } from '../ui/form.js';
import { toast } from '../ui/toast.js';
import { login } from '../core/auth.js';
import { navigate } from '../core/router.js';

export function renderLogin() {
  mount(html`
    <div class="auth">
      <div class="auth__card">
        <div class="auth__brand">
          <div class="topbar__logo">E</div>
          <span>EduCheck AI</span>
        </div>
        <h1 class="auth__title">Вход в систему</h1>
        <p class="auth__subtitle">Проверяйте работы быстрее с ИИ-ассистентом</p>

        <form class="auth__form" id="login-form" novalidate>
          <div class="field">
            <label class="field__label" for="email">Email</label>
            <input class="input" type="email" id="email" name="email" required placeholder="you@example.com" autocomplete="email" />
          </div>
          <div class="field">
            <label class="field__label" for="password">Пароль</label>
            <input class="input" type="password" id="password" name="password" required placeholder="••••••••" autocomplete="current-password" />
          </div>
          <button class="btn btn--primary btn--lg btn--block" type="submit" id="submit-btn">Войти</button>
        </form>

        <div class="auth__footer">
          Нет аккаунта? <a href="#/register">Зарегистрироваться</a>
        </div>
      </div>
    </div>
  `);

  const form = document.getElementById('login-form');
  const btn = document.getElementById('submit-btn');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const { email, password } = readForm(form);
    if (!email || !password) {
      toast('Заполните все поля', 'warning');
      return;
    }
    btn.disabled = true;
    btn.textContent = 'Вход…';
    try {
      const user = await login(email, password);
      toast(`Добро пожаловать, ${user.full_name || user.email}!`, 'success');
      navigate('/');
    } catch (err) {
      toast(err.message || 'Не удалось войти', 'error');
    } finally {
      btn.disabled = false;
      btn.textContent = 'Войти';
    }
  });
}