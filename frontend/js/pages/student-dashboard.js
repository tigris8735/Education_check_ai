import { api } from '../api/index.js';
import { renderLayout } from '../core/layout.js';
import { html, escape, formatDate } from '../ui/render.js';
import { toast } from '../ui/toast.js';

export async function renderStudentDashboard() {
  renderLayout(`<div class="skeleton" style="height:80px"></div>`);
  try {
    const [tasks, submissions] = await Promise.all([
      api.tasks.list().catch(() => []),
      api.submissions.list().catch(() => []),
    ]);

    const content = html`
      <div class="page-header">
        <div class="page-header__title">
          <h1>Мои задания</h1>
          <p class="page-header__subtitle">Активные задания и статус ваших работ</p>
        </div>
      </div>

      <div class="grid grid--3" style="margin-bottom: var(--space-6)">
        <div class="stat">
          <div class="stat__label">Доступно заданий</div>
          <div class="stat__value">${tasks.length}</div>
        </div>
        <div class="stat">
          <div class="stat__label">Сдано работ</div>
          <div class="stat__value">${submissions.length}</div>
        </div>
        <div class="stat">
          <div class="stat__label">Проверено</div>
          <div class="stat__value">${submissions.filter(s => s.status === 'checked').length}</div>
        </div>
      </div>

      <h3 style="margin-bottom: var(--space-3)">Активные задания</h3>
      ${tasks.length === 0
        ? `<div class="card" style="text-align:center;padding:var(--space-8);color:var(--text-muted)">Пока нет заданий</div>`
        : `<div class="grid grid--3">${tasks.map(taskCard).join('')}</div>`}
    `;
    renderLayout(content);
  } catch (err) {
    toast(err.message || 'Ошибка загрузки', 'error');
    renderLayout(`<div class="empty"><div class="empty__title">Не удалось загрузить данные</div></div>`);
  }
}

function taskCard(t) {
  return html`
    <a class="card card--interactive" href="#/tasks/${t.id}">
      <div class="card__header">
        <div class="card__title">${escape(t.title)}</div>
      </div>
      <div class="card__body" style="margin-bottom: var(--space-3)">
        ${escape((t.description || '').slice(0, 120))}${(t.description || '').length > 120 ? '…' : ''}
      </div>
      <div class="card__footer">
        <span class="text-muted" style="font-size:var(--fs-sm)">До ${formatDate(t.deadline)}</span>
        <span class="btn btn--primary btn--sm">Открыть</span>
      </div>
    </a>
  `;
}