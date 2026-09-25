import { api } from '../api/index.js';
import { renderLayout } from '../core/layout.js';
import { html, escape, formatDate } from '../ui/render.js';
import { toast } from '../ui/toast.js';
import { store } from '../core/store.js';

export async function renderStudentDashboard() {
  renderLayout(`<div class="skeleton" style="height:80px"></div>`);
  try {
    const [tasks, submissions, groups] = await Promise.all([
      api.tasks.list().catch(() => []),
      api.submissions.list().catch(() => []),
      api.groups.list().catch(() => []),
    ]);

    const activeTasks = tasks.filter(t => !t.is_expired);
    const expiredTasks = tasks.filter(t => t.is_expired);
    const pending = submissions.filter(s => ['submitted', 'checking'].includes(s.status));
    const aiChecked = submissions.filter(s => s.status === 'checked');
    const reviewed = submissions.filter(s => s.status === 'reviewed');
    const finals = submissions.map(s => s.final_score).filter(v => v != null);
    const avg = finals.length
      ? Math.round(finals.reduce((a, b) => a + b, 0) / finals.length)
      : null;
    const completion = tasks.length
      ? Math.round((submissions.length / tasks.length) * 100)
      : 0;

    const content = html`
      <div class="page-header">
        <div class="page-header__title">
          <h1>Мой дашборд</h1>
          <p class="page-header__subtitle">Привет, ${escape(store.state.user?.first_name || '')}! Вот твой прогресс</p>
        </div>
      </div>

      <div class="grid grid--4 staggered" style="margin-bottom: var(--space-4)">
        <div class="stat">
          <div class="stat__label">Мои группы</div>
          <div class="stat__value">${groups.length}</div>
          <div class="stat__hint">учебных групп</div>
        </div>
        <div class="stat">
          <div class="stat__label">Всего заданий</div>
          <div class="stat__value">${tasks.length}</div>
          <div class="stat__hint">активных: ${activeTasks.length} · истекло: ${expiredTasks.length}</div>
        </div>
        <div class="stat">
          <div class="stat__label">Сдано работ</div>
          <div class="stat__value">${submissions.length}</div>
          <div class="stat__hint">прогресс ${completion}%</div>
        </div>
        <div class="stat">
          <div class="stat__label">Средний балл</div>
          <div class="stat__value">${avg != null ? avg : '—'}</div>
          <div class="stat__hint">по итоговым оценкам</div>
        </div>
      </div>

      <div class="grid grid--4 staggered" style="margin-bottom: var(--space-6)">
        <div class="stat">
          <div class="stat__label">Ожидают проверки</div>
          <div class="stat__value">${pending.length}</div>
          <div class="stat__hint">препод ещё не оценил</div>
        </div>
        <div class="stat">
          <div class="stat__label">Проверено AI</div>
          <div class="stat__value">${aiChecked.length}</div>
          <div class="stat__hint">ждут итоговой оценки</div>
        </div>
        <div class="stat">
          <div class="stat__label">Оценено преподом</div>
          <div class="stat__value">${reviewed.length}</div>
          <div class="stat__hint">с итоговой оценкой</div>
        </div>
        <div class="stat">
          <div class="stat__label">Лучшая работа</div>
          <div class="stat__value">${finals.length ? Math.max(...finals) : '—'}</div>
          <div class="stat__hint">из всех оценок</div>
        </div>
      </div>

      <h3 style="margin-bottom: var(--space-3)">Активные задания</h3>
      ${activeTasks.length === 0
        ? `<div class="card" style="text-align:center;padding:var(--space-8);color:var(--text-muted)">Нет активных заданий 🎉</div>`
        : `<div class="grid grid--3 staggered">${activeTasks.map(taskCard).join('')}</div>`}
    `;

    renderLayout(content);
  } catch (err) {
    toast(err.message || 'Ошибка загрузки', 'error');
    renderLayout(`<div class="empty"><div class="empty__title">Не удалось загрузить данные</div></div>`);
  }
}

function taskCard(t) {
  const attempts = t.max_attempts > 0 ? `${t.submissions_count ?? 0}/${t.max_attempts}` : '∞';
  return html`
    <a class="card card--interactive" href="#/tasks/${t.id}">
      <div class="card__header">
        <div class="card__title">${escape(t.title)}</div>
      </div>
      <div class="card__body" style="margin-bottom: var(--space-3)">
        ${escape((t.description || '').slice(0, 120))}${(t.description || '').length > 120 ? '…' : ''}
      </div>
      <div class="card__footer">
        <span class="badge">до ${formatDate(t.deadline)}</span>
        <span class="text-muted" style="font-size:var(--fs-sm)">попытки: ${attempts}</span>
      </div>
    </a>
  `;
}