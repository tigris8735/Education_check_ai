import { api } from '../api/index.js';
import { renderLayout } from '../core/layout.js';
import { html, escape, formatDate, formatDateTime } from '../ui/render.js';
import { toast } from '../ui/toast.js';
import { openModal } from '../ui/modal.js';
import { readForm } from '../ui/form.js';
import { store } from '../core/store.js';

export async function renderTaskDetail({ id }) {
  renderLayout(`<div class="skeleton" style="height:80px"></div>`);
  try {
    const task = await api.tasks.get(id);
    const isTeacher = store.state.user?.role === 'teacher';

    let submissions = [];
    if (isTeacher) {
      submissions = await api.submissions.listByTask(id).catch(() => []);
    } else {
      submissions = await api.submissions.list({ task_id: id }).catch(() => []);
    }

    const mySubmission = submissions[0];

    const content = html`
      <div class="breadcrumbs">
        <a href="#/tasks">Задания</a>
        <span class="breadcrumbs__sep">/</span>
        <span>${escape(task.title)}</span>
      </div>

      <div class="page-header">
        <div class="page-header__title">
          <h1>${escape(task.title)}</h1>
          <p class="page-header__subtitle">Дедлайн: ${formatDateTime(task.deadline)}</p>
        </div>
        <div class="page-header__actions">
          ${isTeacher ? `
            <button class="btn btn--secondary" id="edit-task">Редактировать</button>
            <button class="btn btn--danger" id="delete-task">Удалить</button>
          ` : `
            <button class="btn btn--primary" id="submit-work">
              ${mySubmission ? 'Изменить работу' : 'Загрузить работу'}
            </button>
          `}
        </div>
      </div>

      <div class="grid grid--2" style="align-items:start">
        <div class="card">
          <h4 style="margin-bottom: var(--space-3)">Описание и критерии</h4>
          <div class="md" style="white-space:pre-wrap">${escape(task.description || '—')}</div>
        </div>

        <div class="card">
          <h4 style="margin-bottom: var(--space-3)">${isTeacher ? 'Сдачи студентов' : 'Моя работа'}</h4>
          ${isTeacher
            ? (submissions.length === 0
              ? `<p class="text-muted">Сдач пока нет.</p>`
              : `<div class="stack stack--sm">${submissions.map(s => `
                <a class="row row--between" style="padding:8px;border:1px solid var(--border);border-radius:8px" href="#/submissions/${s.id}">
                  <span>Работа #${String(s.id).slice(0, 8)}</span>
                  <span class="badge badge--${statusClass(s.status)}">${statusLabel(s.status)}</span>
                </a>
              `).join('')}</div>`)
            : (mySubmission
              ? `<a class="btn btn--secondary btn--block" href="#/submissions/${mySubmission.id}">Открыть мою работу</a>`
              : `<p class="text-muted">Вы ещё не загрузили работу.</p>`)}
        </div>
      </div>
    `;

    renderLayout(content);

    document.getElementById('submit-work')?.addEventListener('click', () => openSubmitModal(task, mySubmission));
    document.getElementById('edit-task')?.addEventListener('click', () => openEditTaskModal(task));
    document.getElementById('delete-task')?.addEventListener('click', async () => {
      if (!confirm('Удалить задание? Это действие необратимо.')) return;
      try {
        await api.tasks.remove(task.id);
        toast('Задание удалено', 'success');
        location.hash = '#/tasks';
      } catch (err) {
        toast(err.message, 'error');
      }
    });
  } catch (err) {
    toast(err.message, 'error');
    renderLayout(`<div class="empty"><div class="empty__title">Задание не найдено</div></div>`);
  }
}

// ⬇️ ИСПРАВЛЕНО: нижний регистр
function statusClass(s) {
  return ({ draft: 'draft', submitted: 'submitted', checking: 'checking', checked: 'checked', failed: 'failed' })[s] || 'draft';
}

function statusLabel(s) {
  return ({ draft: 'Черновик', submitted: 'Сдано', checking: 'AI проверяет', checked: 'AI проверено', failed: 'Ошибка AI' })[s] || s;
}

function openEditTaskModal(task) {
  // Превращаем ISO в datetime-local формат
  const dlValue = task.deadline ? new Date(task.deadline).toISOString().slice(0, 16) : '';

  const { close } = openModal({
    title: 'Редактировать задание',
    size: 'lg',
    body: `
      <form id="edit-task-form" class="stack">
        <div class="field">
          <label class="field__label">Название</label>
          <input class="input" name="title" required value="${escape(task.title || '')}" />
        </div>
        <div class="field">
          <label class="field__label">Описание</label>
          <textarea class="textarea" name="description" rows="6">${escape(task.description || '')}</textarea>
        </div>
        <div class="field">
          <label class="field__label">Дедлайн</label>
          <input class="input" type="datetime-local" name="deadline" value="${dlValue}" />
        </div>
      </form>
    `,
    footer: `
      <button class="btn btn--ghost" data-cancel>Отмена</button>
      <button class="btn btn--primary" data-submit>Сохранить</button>
    `,
  });

  const backdrop = document.querySelector('.modal-backdrop');
  backdrop.querySelector('[data-cancel]').addEventListener('click', close);
  backdrop.querySelector('[data-submit]').addEventListener('click', async () => {
    const form = document.getElementById('edit-task-form');
    const data = readForm(form);
    if (data.deadline) data.deadline = new Date(data.deadline).toISOString();
    else delete data.deadline;

    try {
      await api.tasks.update(task.id, data);
      toast('Задание обновлено', 'success');
      close();
      renderTaskDetail({ id: task.id });
    } catch (err) {
      toast(err.message, 'error');
    }
  });
}

function openSubmitModal(task, existing) {
  const { close } = openModal({
    title: existing ? 'Редактировать работу' : 'Новая работа',
    size: 'lg',
    body: `
      <form id="submission-form" class="stack">
        <div class="field">
          <label class="field__label">Текст работы</label>
          <textarea class="textarea" name="student_comment" rows="10" placeholder="Вставьте текст работы" required>${escape(existing?.student_comment || '')}</textarea>
        </div>
        <div class="field">
          <label class="field__label">Файл (опционально)</label>
          <div class="dropzone" id="dropzone">
            <div class="dropzone__icon">📎</div>
            <div>Перетащите файл или нажмите для выбора</div>
            <input type="file" id="file-input" hidden />
            <div id="file-name" class="text-muted" style="margin-top:8px"></div>
          </div>
        </div>
      </form>
    `,
    footer: `
      <button class="btn btn--ghost" data-cancel>Отмена</button>
      <button class="btn btn--primary" data-submit>${existing ? 'Сохранить' : 'Отправить'}</button>
    `,
  });

  const backdrop = document.querySelector('.modal-backdrop');
  const dz = backdrop.querySelector('#dropzone');
  const fileInput = backdrop.querySelector('#file-input');
  const fileName = backdrop.querySelector('#file-name');

  let file = null;

  dz.addEventListener('click', () => fileInput.click());
  dz.addEventListener('dragover', (e) => { e.preventDefault(); dz.classList.add('is-over'); });
  dz.addEventListener('dragleave', () => dz.classList.remove('is-over'));
  dz.addEventListener('drop', (e) => {
    e.preventDefault(); dz.classList.remove('is-over');
    file = e.dataTransfer.files[0]; if (file) fileName.textContent = file.name;
  });
  fileInput.addEventListener('change', () => {
    file = fileInput.files[0]; if (file) fileName.textContent = file.name;
  });

  backdrop.querySelector('[data-cancel]').addEventListener('click', close);
  backdrop.querySelector('[data-submit]').addEventListener('click', async () => {
    const form = document.getElementById('submission-form');
    const data = readForm(form);
    if (!data.student_comment && !file) { toast('Добавьте текст или файл', 'warning'); return; }

    try {
      if (existing) {
        await api.submissions.update(existing.id, { student_comment: data.student_comment });
      } else {
        const payload = {
          task_id: task.id,
          student_comment: data.student_comment,
        };
        await api.submissions.create(payload);
      }
      toast('Работа отправлена', 'success');
      close();
      renderTaskDetail({ id: task.id });
    } catch (err) {
      toast(err.message, 'error');
    }
  });
}