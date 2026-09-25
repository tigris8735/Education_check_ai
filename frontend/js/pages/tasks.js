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
      : `<div class="grid grid--3 staggered">${tasks.map(t => taskCard(t, isTeacher)).join('')}</div>`}
  `;

  renderLayout(content);
  document.getElementById('create-task')?.addEventListener('click', openCreateTaskModal);
}

function taskCard(t, isTeacher) {
  const progress = isTeacher
    ? `<span class="badge">сдали: ${t.submissions_count ?? 0}/${t.members_count ?? 0}</span>`
    : '';
  const attemptsBadge = t.max_attempts > 0
    ? `<span class="badge">попыток: ${t.max_attempts}</span>`
    : `<span class="badge">∞ попыток</span>`;
  return html`
    <a class="card card--interactive" href="#/tasks/${t.id}">
      <div class="card__header">
        <div class="card__title">${escape(t.title)}</div>
        <span class="badge">${t.is_expired ? 'истекло' : relativeDeadline(t.deadline)}</span>
      </div>
      <div class="card__body" style="margin-bottom:var(--space-3)">
        ${escape((t.description || '').slice(0, 120))}${(t.description || '').length > 120 ? '…' : ''}
      </div>
      <div class="card__footer" style="flex-wrap:wrap;gap:var(--space-2)">
        <span class="badge badge--role">${escape((t.group_names || []).join(', ') || '—')}</span>
        ${attemptsBadge}
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

          <div class="field">
            <label class="field__label">Группы (можно несколько)</label>
            <div class="groups-picker">
              ${groups.map(g => `
                <label class="groups-picker__item">
                  <input type="checkbox" name="group_id" value="${g.id}" />
                  <span>${escape(g.name)}</span>
                  <span class="text-muted" style="font-size:var(--fs-xs)">${g.members_count ?? 0} студ.</span>
                </label>
              `).join('')}
            </div>
            <div class="field__hint">Выберите одну или несколько групп</div>
          </div>

          <div class="grid grid--2">
            <div class="field">
              <label class="field__label">Дедлайн</label>
              <input class="input" type="datetime-local" name="deadline" required />
            </div>
            <div class="field">
              <label class="field__label">Лимит попыток</label>
              <input class="input" type="number" name="max_attempts" min="0" value="0" />
              <div class="field__hint">0 = без ограничений</div>
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
      const checked = [...form.querySelectorAll('input[name="group_id"]:checked')].map(cb => Number(cb.value));
      const title = form.elements.title.value.trim();
      const description = form.elements.description.value;
      const deadline = new Date(form.elements.deadline.value);
      const maxAttempts = Number(form.elements.max_attempts.value || 0);

      if (!title) { toast('Укажите название', 'warning'); return; }
      if (checked.length === 0) { toast('Выберите хотя бы одну группу', 'warning'); return; }
      if (isNaN(deadline.getTime())) { toast('Некорректная дата', 'warning'); return; }

      try {
        await api.tasks.create({
          title, description,
          group_ids: checked,
          deadline: deadline.toISOString(),
          max_attempts: maxAttempts,
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