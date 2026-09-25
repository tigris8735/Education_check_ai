import { api } from '../api/index.js';
import { renderLayout } from '../core/layout.js';
import { html, escape, formatDateTime, relativeDeadline } from '../ui/render.js';
import { toast } from '../ui/toast.js';
import { readForm } from '../ui/form.js';
import { openModal } from '../ui/modal.js';
import { store } from '../core/store.js';

export async function renderTaskDetail({ id }) {
  renderLayout(`<div class="skeleton" style="height:120px"></div>`);
  try {
    const [task, submissions] = await Promise.all([
      api.tasks.get(id),
      api.submissions.list({ task_id: id }).catch(() => []),
    ]);

    const isTeacher = store.state.user?.role === 'teacher';
    const me = store.state.user;

    // У студента: все его попытки по этому заданию
    let myAttempts = [];
    if (!isTeacher) {
      try {
        const allSubs = await api.submissions.list().catch(() => []);
        myAttempts = allSubs.filter(s => s.task_id === task.id && s.student_id === me?.id)
                              .sort((a, b) => new Date(b.submitted_at) - new Date(a.submitted_at));
      } catch {}
    }

    const latestOwn = myAttempts[0];
    const canEdit = latestOwn && !['checking', 'checked', 'reviewed'].includes(latestOwn.status);
    const attemptsUsed = myAttempts.length;
    const attemptsLeft = task.max_attempts > 0 ? task.max_attempts - attemptsUsed : Infinity;
    const canSubmit = !isTeacher && !task.is_expired && attemptsLeft > 0;

    const content = html`
      <div class="breadcrumbs">
        <a href="#/">Главная</a>
        <span class="breadcrumbs__sep">/</span>
        <a href="#/tasks">Задания</a>
        <span class="breadcrumbs__sep">/</span>
        <span>${escape(task.title)}</span>
      </div>

      <div class="page-header">
        <div class="page-header__title">
          <h1>${escape(task.title)}</h1>
          <p class="page-header__subtitle">
            Группы: <span class="badge badge--role">${escape((task.group_names || []).join(', ') || '—')}</span>
            · Дедлайн: ${formatDateTime(task.deadline)}
            ${task.is_expired ? ' · просрочено' : ' · ' + relativeDeadline(task.deadline)}
          </p>
        </div>
        <div class="page-header__actions">
          ${canSubmit ? `<button class="btn btn--primary" id="submit-btn">📤 ${attemptsUsed > 0 ? 'Новая попытка' : 'Сдать работу'}</button>` : ''}
          ${canEdit ? `<button class="btn btn--secondary" id="edit-btn">✏️ Редактировать</button>` : ''}
          ${latestOwn ? `<a class="btn btn--ghost" href="#/submissions/${latestOwn.id}">Последняя работа</a>` : ''}
        </div>
      </div>

      ${!isTeacher && task.max_attempts > 0 ? `
        <div class="card" style="margin-bottom: var(--space-4);background:var(--accent-soft);border-color:transparent">
          <div class="row row--between">
            <div>
              <strong>Лимит попыток</strong>
              <div class="text-muted" style="font-size:var(--fs-sm)">
                Использовано ${attemptsUsed} из ${task.max_attempts}
                ${attemptsLeft > 0 ? ` · осталось ${attemptsLeft}` : ' · попытки исчерпаны'}
              </div>
            </div>
            <div class="progress" style="width:160px">
              <div class="progress__bar" style="width:${Math.min(100, (attemptsUsed / task.max_attempts) * 100)}%"></div>
            </div>
          </div>
        </div>` : ''}

      <div class="card" style="margin-bottom: var(--space-6)">
        <h4 style="margin-bottom: var(--space-3)">Условие задания</h4>
        <div class="md">${escape(task.description || '—')}</div>
      </div>

      ${!isTeacher && myAttempts.length > 1 ? renderAttemptsHistory(myAttempts) : ''}
      ${isTeacher ? renderTeacherSubmissions(submissions) : ''}
    `;

    renderLayout(content);

    document.getElementById('submit-btn')
      ?.addEventListener('click', () => openSubmitModal(task, null));
    document.getElementById('edit-btn')
      ?.addEventListener('click', () => openSubmitModal(task, latestOwn));
  } catch (err) {
    toast(err.message, 'error');
    renderLayout(`<div class="empty"><div class="empty__title">Задание не найдено</div></div>`);
  }
}

function renderAttemptsHistory(attempts) {
  return html`
    <h3 style="margin-bottom: var(--space-3)">История попыток (${attempts.length})</h3>
    <div class="table-wrapper" style="margin-bottom: var(--space-6)">
      <table class="table">
        <thead>
          <tr><th>№</th><th>Статус</th><th>AI</th><th>Итог</th><th>Дата</th></tr>
        </thead>
        <tbody>
          ${attempts.map((s, i) => `
            <tr onclick="location.hash='#/submissions/${s.id}'" style="cursor:pointer">
              <td class="text-mono">Попытка ${i + 1}</td>
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
    </div>
  `;
}

function renderTeacherSubmissions(submissions) {
  if (!submissions.length) {
    return `<div class="card" style="text-align:center;color:var(--text-muted)">Пока нет сдач по этому заданию</div>`;
  }
  return html`
    <h3 style="margin-bottom: var(--space-3)">Сдачи студентов (${submissions.length})</h3>
    <div class="table-wrapper">
      <table class="table">
        <thead>
          <tr><th>Студент</th><th>Группа</th><th>Статус</th><th>AI</th><th>Итог</th><th>Дата</th></tr>
        </thead>
        <tbody>
          ${submissions.map(s => `
            <tr onclick="location.hash='#/submissions/${s.id}'" style="cursor:pointer">
              <td><strong>${escape(s.student_last_name || '')} ${escape(s.student_first_name || '')}</strong></td>
              <td><span class="badge">${escape(s.student_group_name || '—')}</span></td>
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
    </div>
  `;
}

function openSubmitModal(task, existing) {
  const { close } = openModal({
    title: existing ? 'Редактировать работу' : 'Новая работа',
    size: 'lg',
    body: `
      <form id="submission-form" class="stack">
        <div class="field">
          <label class="field__label">Текст работы</label>
          <textarea class="textarea" name="student_comment" rows="10"
            placeholder="Вставьте текст работы">${escape(existing?.student_comment || '')}</textarea>
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
    file = e.dataTransfer.files[0];
    if (file) fileName.textContent = `📄 ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
  });
  fileInput.addEventListener('change', () => {
    file = fileInput.files[0];
    if (file) fileName.textContent = `📄 ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
  });

  backdrop.querySelector('[data-cancel]').addEventListener('click', close);
  backdrop.querySelector('[data-submit]').addEventListener('click', async () => {
    const form = document.getElementById('submission-form');
    const data = readForm(form);
    if (!data.student_comment && !file) { toast('Добавьте текст или файл', 'warning'); return; }

    const btn = backdrop.querySelector('[data-submit]');
    btn.disabled = true;
    btn.textContent = '⏳ Отправка...';

    try {
      let submissionId;
      if (existing) {
        await api.submissions.update(existing.id, { student_comment: data.student_comment });
        submissionId = existing.id;
      } else {
        const created = await api.submissions.create({
          task_id: task.id,
          student_comment: data.student_comment,
        });
        submissionId = created?.id;
      }

      if (file && submissionId) {
        btn.textContent = '⏳ Загрузка файла...';
        const presign = await api.files.presign({
          original_name: file.name,
          content_type: file.type || 'application/octet-stream',
          size: file.size,
        });
        const putRes = await fetch(presign.upload_url, {
          method: 'PUT',
          headers: { 'Content-Type': file.type || 'application/octet-stream' },
          body: file,
        });
        if (!putRes.ok) throw new Error(`Хранилище отклонило файл (HTTP ${putRes.status})`);
        await api.files.confirm(presign.file_id, submissionId);
      }

      toast('Работа отправлена', 'success');
      close();
      renderTaskDetail({ id: task.id });
    } catch (err) {
      toast(err.message, 'error');
      btn.disabled = false;
      btn.textContent = existing ? 'Сохранить' : 'Отправить';
    }
  });
}

function statusClass(s) {
  return ({ draft: 'draft', submitted: 'submitted', checking: 'checking',
            checked: 'checked', reviewed: 'reviewed', failed: 'failed' })[s] || 'draft';
}

function statusLabel(s) {
  return ({ draft: 'Черновик', submitted: 'Сдано', checking: 'AI проверяет',
            checked: 'AI проверено', reviewed: 'Оценено', failed: 'Ошибка' })[s] || s;
}

function scoreClass(v) {
  if (v >= 75) return 'good';
  if (v >= 50) return 'warn';
  return 'bad';
}