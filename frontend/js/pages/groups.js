import { api } from '../api/index.js';
import { renderLayout } from '../core/layout.js';
import { html, escape, formatDate } from '../ui/render.js';
import { toast } from '../ui/toast.js';
import { readForm } from '../ui/form.js';
import { openModal } from '../ui/modal.js';

export async function renderGroups() {
  renderLayout(`<div class="skeleton" style="height:80px"></div>`);
  const groups = await api.groups.list().catch(() => []);

  const content = html`
    <div class="page-header">
      <div class="page-header__title">
        <h1>Группы</h1>
        <p class="page-header__subtitle">Управляйте группами и студентами</p>
      </div>
      <div class="page-header__actions">
        <button class="btn btn--primary" id="create-group">+ Создать группу</button>
      </div>
    </div>

    ${groups.length === 0
      ? `<div class="card" style="text-align:center;padding:var(--space-10);color:var(--text-muted)">Пока нет групп. Создайте первую.</div>`
      : `<div class="grid grid--3">${groups.map(groupCard).join('')}</div>`}
  `;

  renderLayout(content);
  document.getElementById('create-group').addEventListener('click', openCreateGroupModal);
}

function groupCard(g) {
  return html`
    <a class="card card--interactive" href="#/groups/${g.id}">
      <div class="card__header">
        <div class="card__title">${escape(g.name)}</div>
        <span class="badge">${g.members_count ?? 0} участн.</span>
      </div>
      <div class="card__body" style="margin-bottom:var(--space-3)">
        ${escape((g.description || '').slice(0, 90)) || '<span class="text-muted">Без описания</span>'}
      </div>
      <div class="card__meta">Создана ${formatDate(g.created_at)}</div>
    </a>
  `;
}

function openCreateGroupModal() {
  const { close } = openModal({
    title: 'Новая группа',
    body: `
      <form id="group-form" class="stack">
        <div class="field">
          <label class="field__label">Название группы</label>
          <input class="input" name="name" required placeholder="Например, ИУ7-41Б" />
        </div>
        <div class="field">
          <label class="field__label">Описание (опционально)</label>
          <textarea class="textarea" name="description" placeholder="Краткое описание"></textarea>
        </div>
      </form>
    `,
    footer: `
      <button class="btn btn--ghost" data-cancel>Отмена</button>
      <button class="btn btn--primary" data-submit>Создать</button>
    `,
  });

  const backdrop = document.querySelector('.modal-backdrop');
  backdrop.querySelector('[data-cancel]').addEventListener('click', close);
  backdrop.querySelector('[data-submit]').addEventListener('click', async () => {
    const form = document.getElementById('group-form');
    const data = readForm(form);
    if (!data.name) { toast('Укажите название', 'warning'); return; }
    try {
      await api.groups.create(data);
      toast('Группа создана', 'success');
      close();
      renderGroups();
    } catch (err) {
      toast(err.message, 'error');
    }
  });
}