import { api } from '../api/index.js';
import { renderLayout } from '../core/layout.js';
import { html, escape, formatDate } from '../ui/render.js';
import { toast } from '../ui/toast.js';
import { openModal } from '../ui/modal.js';
import { readForm } from '../ui/form.js';

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
        <div class="page-header__actions">
          <button class="btn btn--primary" id="add-student">+ Добавить студента</button>
          <button class="btn btn--secondary" id="create-task-for-group">+ Задание для группы</button>
        </div>
      </div>

      <div class="grid grid--2" style="align-items:start">
        <div class="card">
          <h4 style="margin-bottom: var(--space-4)">Участники (${(g.members?.length ?? 0)})</h4>
          ${(g.members?.length ?? 0) === 0
            ? `<p class="text-muted">Пока нет участников</p>`
            : `<div class="stack stack--sm">
              ${g.members.map(m => `
                <div class="row row--between" style="padding:8px;border-bottom:1px solid var(--border)">
                  <div>
                    <strong>${escape(m.full_name || (m.first_name ? `${m.first_name} ${m.last_name || ''}`.trim() : '—'))}</strong>
                    <div class="text-muted" style="font-size:var(--fs-sm)">${escape(m.email || '')}</div>
                  </div>
                  <button class="btn btn--danger btn--sm" data-remove="${m.student_id || m.id}">Удалить</button>
                </div>
              `).join('')}
            </div>`}
        </div>

        <div class="card">
          <h4 style="margin-bottom: var(--space-4)">О группе</h4>
          <p>${escape(g.description || 'Описание не задано')}</p>
        </div>
      </div>
    `;

    renderLayout(content);

    document.querySelectorAll('[data-remove]').forEach(btn => {
      btn.addEventListener('click', async () => {
        const sid = btn.getAttribute('data-remove');
        if (!confirm('Удалить участника из группы?')) return;
        try {
          await api.groups.removeMember(id, sid);
          toast('Участник удалён', 'success');
          renderGroupDetail({ id });
        } catch (err) {
          toast(err.message, 'error');
        }
      });
    });

    document.getElementById('add-student')?.addEventListener('click', () => openAddStudentModal(id));
    document.getElementById('create-task-for-group')?.addEventListener('click', () => {
      location.hash = `#/tasks`;
    });
  } catch (err) {
    toast(err.message, 'error');
    renderLayout(`<div class="empty"><div class="empty__title">Группа не найдена</div></div>`);
  }
}

function openAddStudentModal(groupId) {
  const { close } = openModal({
    title: 'Добавить студента',
    body: `
      <form id="add-student-form" class="stack">
        <div class="field">
          <label class="field__label">Имя</label>
          <input class="input" name="first_name" required placeholder="Иван" />
        </div>
        <div class="field">
          <label class="field__label">Фамилия</label>
          <input class="input" name="last_name" required placeholder="Иванов" />
        </div>
        <div class="field">
          <label class="field__label">Email</label>
          <input class="input" type="email" name="email" required placeholder="ivan@example.com" />
        </div>
        <div class="field">
          <label class="field__label">Пароль (временный)</label>
          <input class="input" type="password" name="password" required minlength="8" placeholder="Минимум 8 символов" />
        </div>
        <div class="card card--info" style="padding: var(--space-3); background: var(--bg-muted)">
          <small>Аккаунт студента будет создан автоматически и он сразу попадёт в группу.</small>
        </div>
      </form>
    `,
    footer: `
      <button class="btn btn--ghost" data-cancel>Отмена</button>
      <button class="btn btn--primary" data-submit>Добавить</button>
    `,
  });

  const backdrop = document.querySelector('.modal-backdrop');
  backdrop.querySelector('[data-cancel]').addEventListener('click', close);
  backdrop.querySelector('[data-submit]').addEventListener('click', async () => {
    const form = document.getElementById('add-student-form');
    const data = readForm(form);
    if (!data.first_name || !data.last_name || !data.email || !data.password) {
      toast('Заполните все поля', 'warning');
      return;
    }

    try {
      // 1. Регистрируем студента
      const regResult = await api.auth.register({
        first_name: data.first_name,
        last_name: data.last_name,
        email: data.email,
        password: data.password,
        role: 'student',
      });

      const studentId = regResult?.user?.id;
      if (!studentId) throw new Error('Не удалось получить ID студента');

      // 2. Добавляем его в группу
      await api.groups.addMember(groupId, studentId);

      toast('Студент добавлен в группу', 'success');
      close();
      renderGroupDetail({ id: groupId });
    } catch (err) {
      toast(err.message, 'error');
    }
  });
}