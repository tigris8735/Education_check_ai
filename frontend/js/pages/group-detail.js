import { api } from '../api/index.js';
import { renderLayout } from '../core/layout.js';
import { html, escape, formatDate } from '../ui/render.js';
import { toast } from '../ui/toast.js';

export async function renderGroupDetail({ id }) {
  renderLayout(`<div class="skeleton" style="height:120px"></div>`);
  try {
    const g = await api.groups.get(id);
    const content = html`
      <div class="breadcrumbs">
        <a href="#/groups">Группы</a>
        <span class="breadcrumbs__sep">/</span>
        <span>${escape(g.name)}</span>
      </div>

      <div class="page-header">
        <div class="page-header__title">
          <h1>${escape(g.name)}</h1>
          <p class="page-header__subtitle">Создана ${formatDate(g.created_at)} · ${(g.members?.length ?? 0)} участников</p>
        </div>
      </div>

      <div class="card">
        <h4 style="margin-bottom: var(--space-4)">Участники</h4>
        ${(g.members?.length ?? 0) === 0
          ? `<p class="text-muted">Пока нет участников</p>`
          : `<div class="stack stack--sm">
              ${g.members.map(m => `
                <div class="row row--between" style="padding:8px;border-bottom:1px solid var(--border)">
                  <span>${escape(m.full_name || m.email || m.student_id || m.id)}</span>
                  <button class="btn btn--danger btn--sm" data-remove="${m.student_id || m.id}">Удалить</button>
                </div>
              `).join('')}
            </div>`}
      </div>
    `;
    renderLayout(content);

    document.querySelectorAll('[data-remove]').forEach(btn => {
      btn.addEventListener('click', async () => {
        const sid = btn.getAttribute('data-remove');
        try {
          await api.groups.removeMember(id, sid);
          toast('Участник удалён', 'success');
          renderGroupDetail({ id });
        } catch (err) {
          toast(err.message, 'error');
        }
      });
    });
  } catch (err) {
    toast(err.message, 'error');
    renderLayout(`<div class="empty"><div class="empty__title">Группа не найдена</div></div>`);
  }
}