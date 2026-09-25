import { api } from '../api/index.js';
import { renderLayout } from '../core/layout.js';
import { html, formatDateTime } from '../ui/render.js';

export async function renderSubmissions() {
  renderLayout(`<div class="skeleton" style="height:80px"></div>`);
  const items = await api.submissions.list().catch(() => []);

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
                  <td>#${s.task_id}</td>
                  <td><span class="badge badge--${statusClass(s.status)}">${statusLabel(s.status)}</span></td>
                  <td>${s.ai_score ?? '—'}</td>
                  <td><strong>${s.final_score ?? '—'}</strong></td>
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