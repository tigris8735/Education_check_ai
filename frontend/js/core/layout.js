import { store } from './store.js';
import { html, initials, escape } from '../ui/render.js';
import { logout } from './auth.js';

export function renderLayout(content) {
  const user = store.state.user || {};
  const role = user.role || '';
  const nav = role === 'TEACHER' ? teacherNav() : role === 'STUDENT' ? studentNav() : [];

  document.getElementById('app').innerHTML = html`
    <header class="topbar">
      <button class="btn btn--ghost btn--sm" id="sidebar-toggle" style="display:none">☰</button>
      <a href="#/" class="topbar__brand">
        <div class="topbar__logo">E</div>
        <span>EduCheck AI</span>
      </a>
      <div class="topbar__spacer"></div>
      <div class="topbar__actions">
        <span class="badge badge--role">${role}</span>
        <div class="avatar" title="${escape(user.full_name || user.email || '')}">
          ${initials(user.full_name || user.email || '?')}
        </div>
        <button class="btn btn--ghost btn--sm" id="logout-btn">Выйти</button>
      </div>
    </header>

    <div class="layout">
      <aside class="sidebar" id="sidebar">
        ${nav}
      </aside>
      <main class="main">
        <div class="container" id="page-content">
          ${content}
        </div>
      </main>
    </div>
  `;

  document.getElementById('logout-btn').addEventListener('click', () => {
    logout();
  });

  // toggle sidebar on mobile
  const sidebar = document.getElementById('sidebar');
  const toggle = document.getElementById('sidebar-toggle');
  if (window.innerWidth <= 900) toggle.style.display = 'inline-flex';
  toggle?.addEventListener('click', () => sidebar.classList.toggle('is-open'));

  // Активный пункт по хэшу
  const path = location.hash || '#/';
  document.querySelectorAll('.sidebar__link').forEach(a => {
    if (a.getAttribute('href') === path) a.classList.add('is-active');
  });
}

function teacherNav() {
  return html`
    <div class="sidebar__section">Преподаватель</div>
    <a class="sidebar__link" href="#/">Дашборд</a>
    <a class="sidebar__link" href="#/groups">Группы</a>
    <a class="sidebar__link" href="#/tasks">Задания</a>
    <div class="sidebar__section">Работы</div>
    <a class="sidebar__link" href="#/submissions">На проверку</a>
  `;
}

function studentNav() {
  return html`
    <div class="sidebar__section">Студент</div>
    <a class="sidebar__link" href="#/">Дашборд</a>
    <a class="sidebar__link" href="#/tasks">Мои задания</a>
    <a class="sidebar__link" href="#/submissions">Мои работы</a>
  `;
}