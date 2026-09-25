import { store } from './store.js';
import { html, initials, escape } from '../ui/render.js';
import { logout } from './auth.js';
import { toggleTheme, getStoredTheme } from './theme.js';

const ICONS = {
  dashboard: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="9"/><rect x="14" y="3" width="7" height="5"/><rect x="14" y="12" width="7" height="9"/><rect x="3" y="16" width="7" height="5"/></svg>',
  groups: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
  tasks: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="9" y1="15" x2="15" y2="15"/></svg>',
  check: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>',
  works: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>',
};

export function renderLayout(content) {
  const user = store.state.user || {};
  const role = user.role || '';
  const nav = role === 'teacher' ? teacherNav() : role === 'student' ? studentNav() : [];
  const theme = getStoredTheme();
  const themeIcon = theme === 'dark' ? '☀️' : '🌙';

  document.getElementById('app').innerHTML = html`
    <header class="topbar">
      <button class="btn btn--ghost btn--sm" id="sidebar-toggle" style="display:none">☰</button>
      <a href="#/" class="topbar__brand">
        <div class="topbar__logo">E</div>
        <span>EduCheck AI</span>
      </a>
      <div class="topbar__spacer"></div>
      <div class="topbar__actions">
        <button class="btn btn--ghost btn--sm" id="theme-toggle" title="Переключить тему">
          ${themeIcon}
        </button>
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

  document.getElementById('logout-btn').addEventListener('click', () => logout());

  document.getElementById('theme-toggle').addEventListener('click', () => {
    const newTheme = toggleTheme();
    document.getElementById('theme-toggle').textContent = newTheme === 'dark' ? '☀️' : '🌙';
  });

  const sidebar = document.getElementById('sidebar');
  const toggle = document.getElementById('sidebar-toggle');
  if (window.innerWidth <= 900) toggle.style.display = 'inline-flex';
  toggle?.addEventListener('click', () => sidebar.classList.toggle('is-open'));

  const path = location.hash || '#/';
  document.querySelectorAll('.sidebar__link').forEach(a => {
    if (a.getAttribute('href') === path) a.classList.add('is-active');
  });
}

function link(icon, href, text) {
  return `<a class="sidebar__link" href="${href}">${ICONS[icon]}<span>${text}</span></a>`;
}

function teacherNav() {
  return html`
    <div class="sidebar__section">Преподаватель</div>
    ${link('dashboard', '#/', 'Дашборд')}
    ${link('groups', '#/groups', 'Группы')}
    ${link('tasks', '#/tasks', 'Задания')}
    ${link('check', '#/submissions', 'На проверку')}
  `;
}

function studentNav() {
  return html`
    <div class="sidebar__section">Студент</div>
    ${link('dashboard', '#/', 'Дашборд')}
    ${link('tasks', '#/tasks', 'Мои задания')}
    ${link('works', '#/submissions', 'Мои работы')}
  `;
}