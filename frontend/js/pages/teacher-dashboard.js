import { api } from '../api/index.js';
import { renderLayout } from '../core/layout.js';
import { html, escape, formatDate, relativeDeadline } from '../ui/render.js';
import { toast } from '../ui/toast.js';

export async function renderTeacherDashboard() {
  renderLayout(`<div class="skeleton" style="height:80px"></div>`);
  try {
    const [groups, tasks, submissions] = await Promise.all([
      api.groups.list().catch(() => []),
      api.tasks.list().catch(() => []),
      api.submissions.list().catch(() => []),
    ]);

    const pending = submissions.filter(s => s.status === 'SUBMITTED' || s.status === 'CHECKED');
    const reviewed = submissions.filter(s => s.status === 'REVIEWED').length;

    const content = html`
      <div class="page-header">
        <div class="page-header__title">
          <h1>Дашборд преподавателя</h1>
          <p class="page-header__subtitle">Обзор групп, заданий и работ студентов</p>
        </div>
        <div class="page-header__actions">
          <a class="btn btn--primary" href="#/tasks">+ Новое задание</a>
        </div>
      </div>

      <div class="grid grid--4" style="margin-bottom: var(--space-6)">
        <div class="stat">
          <div class="stat__label">Группы</div>
          <div class="stat__value">${groups.length}</div>
        </div>
        <div class="stat">
          <div class="stat__label">Задания</div>
          <div class="stat__value">${tasks.length}</div>
        </div>
        <div class="stat">
          <div class="stat__label">На проверку</div>
          <div class="stat__value">${pending.length}</div>
        </div>
        <div class="stat">
          <div class="stat__label">Проверено</div>
          <div class="stat__value">${reviewed}</div>
        </div>
      </div>

      <div class="grid grid--2">
        <section>
          <div class="row row--between" style="margin-bottom: var(--space-3)">
            <h3>Последние задания</h3>
            <a class="btn btn--ghost btn--sm" href="#/tasks">Все →</a>
          </div>
          ${tasks.length === 0 ? emptyBlock('Пока нет заданий') : tasks.slice(0, 5).map(taskCard).join('')}
        </section>

        <section>
          <div class="row row--between" style="margin-bottom: var(--space-3)">
            <h3>Работы на проверку</h3>
            <a class="btn btn--ghost btn--sm" href="#/submissions">Все →</a>
          </div>
          ${pending.length === 0 ? emptyBlock('Нет работ на проверку') : pending.slice(0, 5).map(subCard).join('')}
        </section>
      </div>
    `;
    renderLayout(content);
  } catch (err) {
    toast(err.message || 'Ошибка загрузки', 'error');
    renderLayout(`<div class="empty"><div class="empty__title">Не удалось загрузить данные</div></div>`);
  }
}

function taskCard(t) {
  return html`
    <a class="card card--interactive" href="#/tasks/${t.id}" style="display:block; margin-bottom: var(--space-3)">
      <div class="card__header">
        <div class="card__title">${escape(t.title)}</div>
        <span class="badge">${t.deadline ? relativeDeadline(t.deadline) : 'без дедлайна'}</span>
      </div>
      <div class="card__meta">Дедлайн: ${formatDate(t.deadline)}</div>
    </a>
  `;
}

function subCard(s) {
  const badge = statusBadge(s.status);
  return html`
    <a class="card card--interactive" href="#/submissions/${s.id}" style="display:block; margin-bottom: var(--space-3)">
      <div class="card__header">
        <div class="card__title">Работа #${s.id.slice(0, 8)}</div>
        ${badge}
      </div>
      <div class="card__meta">Студент ID: ${escape(s.student_id || '—')}</div>
    </a>
  `;
}

function statusBadge(status) {
  const map = {
    DRAFT: ['draft', 'Черновик'],
    SUBMITTED: ['submitted', 'Сдано'],
    CHECKING: ['checking', 'AI проверяет'],
    CHECKED: ['checked', 'AI проверено'],
    REVIEWED: ['reviewed', 'Проверено'],
    FAILED: ['failed', 'Ошибка AI'],
  };
  const [cls, label] = map[status] || ['draft', status];
  return `<span class="badge badge--${cls}">${label}</span>`;
}

function emptyBlock(text) {
  return `<div class="card" style="text-align:center; color:var(--text-muted); padding: var(--space-8)">${text}</div>`;
}