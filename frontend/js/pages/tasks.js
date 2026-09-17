import { api } from '../api/index.js';
import { renderLayout } from '../core/layout.js';
import { html, escape, formatDate, relativeDeadline } from '../ui/render.js';
import { toast } from '../ui/toast.js';
import { openModal } from '../ui/modal.js';
import { readForm } from '../ui/form.js';
import { store } from '../core/store.js';

export async function renderTasks() {
  renderLayout(`<div class="skeleton" style="height:80px"></div>`);
  const [tasks, groups] = await Promise.all([
    api.tasks.list().catch(() => []),
    store.state.user?.role === 'TEACHER' ? api.groups.list().catch(() => []) : Promise.resolve([]),
  ]);

  const content = html`
    <div class="page-header">
      <div class="page-header__title">
        <h1>Задания</h1>
        <p class="page-header__subtitle">Все задания и дедлайны</p>
      </div>
      ${store.state.user?.role === 'TEACHER' ? `
        <div class="page-header__actions">
          <button class="btn btn--primary" id="create-task">+ Новое задание</button>
        </div>
      ` : ''}
    </div>

    ${tasks.length === 0
      ? `<div class="card" style="text-align:center;padding:var(--space-10);color:var(--text-muted)">Пока нет заданий</div>`
      : `<div class="grid grid--3">${tasks.map(taskCard).join('')}</div>`}
  `;
  renderLayout(content);

  document.getElementById('create-task')?.addEventListener('click', () => openCreateTaskModal(groups));
}

function taskCard(t) {
  return html`
    <a class="card card--interactive" href="#/tasks/${t.id}">
      <div class="card__header">
        <div class="card__title">${escape(t.title)}</div>
        <span class="badge">${relativeDeadline(t.deadline)}</span>
      </div>
      <div class="card__body">${escape((t.description || '').slice(0, 140))}</div>
      <div class="card__footer">
        <span class="text-muted" style="font-size:var(--fs-sm)">до ${formatDate(t.deadline)}</span>
        <span class="text-accent" style="font-size:var(--fs-sm)">Открыть →</span>
      </div>
    </a>
  `;
}

function openCreateTaskModal(groups) {
  const groupOptions = groups.map(g =>
    `<option value="${g.id}">${escape(g.name)}</option>`
  ).join('');

  const { close } = openModal({
    title: 'Новое задание',
    size: 'lg',
    body: `
      <form id="task-form" class="stack">
        <div class="field">
          <label class="field__label">Название</label>
          <input class="input" name="title" required placeholder="Например, Эссе по истории" />
        </div>
        <div class="field">
          <label class="field__label">Описание и критерии</label>
          <textarea class="textarea" name="description" rows="6" placeholder="Опишите требования и критерии оценки — они будут использованы для AI-проверки"></textarea>
        </div>
        <div class="grid grid--2">
          <div class="field">
            <label class="field__label">Дедлайн</label>
            <input class="input" type="datetime-local" name="deadline" />
          </div>
          <div class="field">
            <label class="field__label">Группа</label>
            <select class="select" name="group_id">
              <option value="">— Не выбрана —</option>
              ${groupOptions}
            </select>
          </div>
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
    const form = document.getElementById('task-form');
    const data = readForm(form);
    if (!data.title) { toast('Укажите название', 'warning'); return; }
    if (!data.group_id) delete data.group_id;
    if (!data.deadline) delete data.deadline;
    try {
      await api.tasks.create(data);
      toast('Задание создано', 'success');
      close();
      renderTasks();
    } catch (err) {
      toast(err.message, 'error');
    }
  });
}