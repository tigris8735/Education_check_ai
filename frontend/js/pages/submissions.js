import { api } from '../api/index.js';
import { renderLayout } from '../core/layout.js';
import { html, escape, formatDateTime } from '../ui/render.js';
import { store } from '../core/store.js';

export async function renderSubmissions() {
  renderLayout(`<div class="skeleton" style="height:80px"></div>`);
  const isTeacher = store.state.user?.role === 'teacher';
  const items = await api.submissions.list().catch(() => []);

  if (isTeacher) return renderTeacherQueue(items);
  return renderStudentTable(items);
}

/* ---------- Преподаватель: очередь на проверку ---------- */
function renderTeacherQueue(items) {
  const queue = items
    .filter(s => ['submitted', 'checking', 'checked'].includes(s.status))
    .sort((a, b) => new Date(b.submitted_at || b.created_at) - new Date(a.submitted_at || a.created_at));

  const content = html`
    <div class="page-header">
      <div class="page-header__title">
        <h1>На проверку</h1>
        <p class="page-header__subtitle">Работы, ожидающие вашего решения (${queue.length})</p>
      </div>
    </div>

    ${queue.length === 0
      ? `<div class="card" style="text-align:center;padding:var(--space-10);color:var(--text-muted)">Нет работ на проверку</div>`
      : `<div class="grid grid--3">${queue.map(queueCard).join('')}</div>`}
  `;

  renderLayout(content);
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
        <span class="text-muted" style="font-size:var(--fs-sm)">
          AI: ${s.ai_score ?? '—'} · Итог: ${s.final_score ?? '—'}
        </span>
      </div>
    </a>
  `;
}

/* ---------- Студент: таблица своих работ ---------- */
function renderStudentTable(items) {
  const content = html`
    <div class="page-header">
      <div class="page-header__title">
        <h1>Мои работы</h1>
        <p class="page-header__subtitle">Все ваши сдачи и их статусы</p>
      </div>
    </div>

    ${items.length === 0
      ? `<div class="card" style="text-align:center;padding:var(--space-10);color:var(--text-muted)">Работ пока нет</div>`
      : `
        <div class="table-wrapper">
          <table class="table">
            <thead>
              <tr><th>Задание</th><th>Статус</th><th>AI-оценка</th><th>Итог</th><th>Дата</th></tr>
            </thead>
            <tbody>
              ${items.map(s => `
                <tr onclick="location.hash='#/submissions/${s.id}'" style="cursor:pointer">
                  <td>${escape(s.task_title || '#' + s.task_id)}</td>
                  <td><span class="badge badge--${statusClass(s.status)}">${statusLabel(s.status)}</span></td>
                  <td>${s.ai_score ?? '—'}</td>
                  <td>${s.final_score != null
                    ? `<span class="score score--${scoreClass(s.final_score)}"><span class="score__value">${s.final_score}</span></span>`
                    : '—'}</td>
                  <td class="text-muted">${formatDateTime(s.submitted_at || s.created_at)}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>`}
  `;

  renderLayout(content);
}

function statusClass(s) {
  return ({ draft: 'draft', submitted: 'submitted', checking: 'checking',
            checked: 'checked', reviewed: 'reviewed', failed: 'failed' })[s] || 'draft';
}

function statusLabel(s) {
  return ({ draft: 'Черновик', submitted: 'Сдано', checking: 'AI проверяет',
            checked: 'AI проверено', reviewed: 'Оценено преподом', failed: 'Ошибка AI' })[s] || s;
}

function scoreClass(v) {
  if (v >= 75) return 'good';
  if (v >= 50) return 'warn';
  return 'bad';
}