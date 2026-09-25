import { api } from '../api/index.js';
import { renderLayout } from '../core/layout.js';
import { html, escape, formatDate, relativeDeadline } from '../ui/render.js';
import { toast } from '../ui/toast.js';
import { readForm } from '../ui/form.js';
import { openModal } from '../ui/modal.js';
import { store } from '../core/store.js';

export async function renderTasks() {
  renderLayout(`<div class="skeleton" style="height:80px"></div>`);
  const isTeacher = store.state.user?.role === 'teacher';
  const tasks = await api.tasks.list().catch(() => []);

  const content = html`
    <div class="page-header">
      <div class="page-header__title">
        <h1>${isTeacher ? 'Задания' : 'Мои задания'}</h1>
        <p class="page-header__subtitle">${isTeacher ? 'Все задания и дедлайны' : 'Задания ваших групп'}</p>
      </div>
      ${isTeacher ? `
        <div class="page-header__actions">
          <button class="btn btn--primary" id="create-task">+ Новое задание</button>
        </div>` : ''}
    </div>

    ${tasks.length === 0
      ? `<div class="card" style="text-align:center;padding:var(--space-10);color:var(--text-muted)">Заданий пока нет</div>`
      : `<div class="grid grid--3">${tasks.map(t => taskCard(t, isTeacher)).join('')}</div>`}
  `;

  renderLayout(content);
  document.getElementById('create-task')?.addEventListener('click', openCreateTaskModal);
}

function taskCard(t, isTeacher) {
  const progress = isTeacher
    ? `<span class="badge">выполнили: ${t.submissions_count ?? 0}/${t.members_count ?? 0}</span>`
    : '';
  return html`
    <a class="card card--interactive" href="#/tasks/${t.id}">
      <div class="card__header">
        <div class="card__title">${escape(t.title)}</div>
        <span class="badge">${t.is_expired ? 'истекло' : relativeDeadline(t.deadline)}</span>
      </div>
      <div class="card__body" style="margin-bottom:var(--space-3)">
        ${escape((t.description || '').slice(0, 120))}${(t.description || '').length > 120 ? '…' : ''}
      </div>
      <div class="card__footer">
        <span class="badge">${escape(t.group_name || 'группа не указана')}</span>
        ${progress}
        <span class="text-muted" style="font-size:var(--fs-sm)">до ${formatDate(t.deadline)}</span>
      </div>
    </a>
  `;
}

function openCreateTaskModal() {
  api.groups.list().then(groups => {
    const { close } = openModal({
      title: 'Новое задание',
      size: 'lg',
      body: `
        <form id="task-form" class="stack">
          <div class="field">
            <label class="field__label">Название</label>
            <input class="input" name="title" required placeholder="Например: Лабораторная №3" />
          </div>
          <div class="field">
            <label class="field__label">Описание</label>
            <textarea class="textarea" name="description" placeholder="Условие задания"></textarea>
          </div>
          <div class="grid grid--2">
            <div class="field">
              <label class="field__label">Группа</label>
              <select class="select" name="group_id" required>
                ${groups.map(g => `<option value="${g.id}">${escape(g.name)}</option>`).join('')}
              </select>
            </div>
            <div class="field">
              <label class="field__label">Дедлайн</label>
              <input class="input" type="datetime-local" name="deadline" required />
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
      if (!data.title || !data.deadline || !data.group_id) {
        toast('Заполните название, группу и дедлайн', 'warning'); return;
      }
      const deadline = new Date(data.deadline);
      if (isNaN(deadline.getTime())) { toast('Некорректная дата', 'warning'); return; }

      try {
        await api.tasks.create({
          title: data.title,
          description: data.description || '',
          group_id: Number(data.group_id),
          deadline: deadline.toISOString(),
        });
        toast('Задание создано', 'success');
        close();
        renderTasks();
      } catch (err) {
        toast(err.message, 'error');
      }
    });
  }).catch(err => toast(err.message, 'error'));
}