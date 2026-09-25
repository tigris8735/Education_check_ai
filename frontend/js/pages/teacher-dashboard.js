import { api } from '../api/index.js';
import { renderLayout } from '../core/layout.js';
import { html, escape } from '../ui/render.js';
import { toast } from '../ui/toast.js';

export async function renderTeacherDashboard() {
  renderLayout(`<div class="skeleton" style="height:80px"></div>`);
  try {
    const [groups, tasks, subs] = await Promise.all([
      api.groups.list().catch(() => []),
      api.tasks.list().catch(() => []),
      api.submissions.list().catch(() => []),
    ]);

    const details = await Promise.all(groups.map(g => api.groups.get(g.id).catch(() => null)));
    const studentIds = new Set();
    details.forEach(g => g?.members?.forEach(m => studentIds.add(m.id)));

    const activeTasks = tasks.filter(t => !t.is_expired);
    const expiredTasks = tasks.filter(t => t.is_expired);
    const queueAll = subs
      .filter(s => ['submitted', 'checking', 'checked'].includes(s.status))
      .sort((a, b) => new Date(b.submitted_at || b.created_at) - new Date(a.submitted_at || a.created_at));
    const queue = queueAll.slice(0, 3);
    const aiChecked = subs.filter(s => s.status === 'checked');
    const reviewed = subs.filter(s => s.status === 'reviewed');
    const finals = subs.map(s => s.final_score).filter(v => v != null);
    const avg = finals.length
      ? Math.round(finals.reduce((a, b) => a + b, 0) / finals.length)
      : null;

    const content = html`
      <div class="page-header">
        <div class="page-header__title">
          <h1>Дашборд преподавателя</h1>
          <p class="page-header__subtitle">Сводка по вашим группам, заданиям и работам</p>
        </div>
      </div>

      <div class="grid grid--4 staggered" style="margin-bottom: var(--space-4)">
        <div class="stat">
          <div class="stat__label">Группы</div>
          <div class="stat__value">${groups.length}</div>
          <div class="stat__hint">ведёте сейчас</div>
        </div>
        <div class="stat">
          <div class="stat__label">Студенты</div>
          <div class="stat__value">${studentIds.size}</div>
          <div class="stat__hint">уникальных во всех группах</div>
        </div>
        <div class="stat">
          <div class="stat__label">Задания</div>
          <div class="stat__value">${tasks.length}</div>
          <div class="stat__hint">активных: ${activeTasks.length} · истекло: ${expiredTasks.length}</div>
        </div>
        <div class="stat">
          <div class="stat__label">Сдано работ</div>
          <div class="stat__value">${subs.length}</div>
          <div class="stat__hint">всего за всё время</div>
        </div>
      </div>

      <div class="grid grid--4 staggered" style="margin-bottom: var(--space-6)">
        <div class="stat">
          <div class="stat__label">На проверку</div>
          <div class="stat__value">${queueAll.length}</div>
          <div class="stat__hint">ожидают вашего решения</div>
        </div>
        <div class="stat">
          <div class="stat__label">Проверено AI</div>
          <div class="stat__value">${aiChecked.length}</div>
          <div class="stat__hint">ждут итоговой оценки</div>
        </div>
        <div class="stat">
          <div class="stat__label">Оценено вами</div>
          <div class="stat__value">${reviewed.length}</div>
          <div class="stat__hint">с итоговой оценкой</div>
        </div>
        <div class="stat">
          <div class="stat__label">Средний балл</div>
          <div class="stat__value">${avg != null ? avg : '—'}</div>
          <div class="stat__hint">по итоговым оценкам</div>
        </div>
      </div>

      <h3 style="margin-bottom: var(--space-3)">Отправлены на проверку</h3>
      ${queue.length === 0
        ? `<div class="card" style="text-align:center;padding:var(--space-8);color:var(--text-muted)">Нет работ на проверку 🎉</div>`
        : `<div class="grid grid--3 staggered">${queue.map(queueCard).join('')}</div>`}
    `;

    renderLayout(content);
  } catch (err) {
    toast(err.message || 'Ошибка загрузки', 'error');
    renderLayout(`<div class="empty"><div class="empty__title">Не удалось загрузить данные</div></div>`);
  }
}

function queueCard(s) {
  return html`
    <a class="card card--interactive" href="#/submissions/${s.id}">
      <div class="card__header">
        <div class="card__title">${escape(s.student_last_name || '')} ${escape(s.student_first_name || '')}</div>
        <span class="badge badge--${statusClass(s.status)}">${statusLabel(s.status)}</span>
      </div>
      <div class="card__body" style="margin-bottom:var(--space-3)">
        ${escape(s.task_title || 'Задание #' + s.task_id)}
      </div>
      <div class="card__footer">
        <span class="badge">${escape(s.student_group_name || '—')}</span>
        <span class="text-muted" style="font-size:var(--fs-sm)">AI: ${s.ai_score ?? '—'}</span>
      </div>
    </a>
  `;
}

function statusClass(s) {
  return ({ draft: 'draft', submitted: 'submitted', checking: 'checking',
            checked: 'checked', reviewed: 'reviewed', failed: 'failed' })[s] || 'draft';
}

function statusLabel(s) {
  return ({ draft: 'Черновик', submitted: 'Сдано', checking: 'AI проверяет',
            checked: 'AI проверено', reviewed: 'Оценено', failed: 'Ошибка' })[s] || s;
}