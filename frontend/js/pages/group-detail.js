import { api } from '../api/index.js';
import { renderLayout } from '../core/layout.js';
import { html, escape, formatDate, formatDateTime } from '../ui/render.js';
import { toast } from '../ui/toast.js';
import { readForm } from '../ui/form.js';
import { openModal } from '../ui/modal.js';

export async function renderGroupDetail({ id }) {
  renderLayout(`<div class="skeleton" style="height:120px"></div>`);
  try {
    const [g, tasks] = await Promise.all([
      api.groups.get(id),
      api.tasks.listByGroup(id).catch(() => []),
    ]);

    // сдачи по каждому заданию группы
    const subsByTask = await Promise.all(
      tasks.map(t => api.submissions.listByTask(t.id).catch(() => []))
    );

    // агрегат по студентам: выполнено заданий + баллы
    const perStudent = {};
    tasks.forEach((t, i) => {
      (subsByTask[i] || []).forEach(s => {
        const e = perStudent[s.student_id] ??= { done: new Set(), scores: [] };
        e.done.add(t.id);
        const sc = s.final_score ?? s.ai_score;
        if (sc != null) e.scores.push(sc);
      });
    });

    const members = g.members || [];

    const content = html`
      <div class="breadcrumbs">
        <a href="#/groups">Группы</a>
        <span class="breadcrumbs__sep">/</span>
        <span>${escape(g.name)}</span>
      </div>

      <div class="page-header">
        <div class="page-header__title">
          <h1>${escape(g.name)}</h1>
          <p class="page-header__subtitle">
            Создана ${formatDate(g.created_at)} · ${members.length} участников · ${tasks.length} заданий
          </p>
        </div>
        <div class="page-header__actions">
          <button class="btn btn--primary" id="add-student">+ Добавить студента</button>
        </div>
      </div>

      <div class="grid grid--2" style="align-items:start">
        <div class="card">
          <h4 style="margin-bottom: var(--space-4)">Участники (${members.length})</h4>
          ${members.length === 0
            ? `<p class="text-muted">Пока нет участников</p>`
            : `<div class="stack stack--sm">
              ${members.map(m => {
                const st = perStudent[m.id];
                const done = st ? st.done.size : 0;
                const avg = st && st.scores.length
                  ? Math.round(st.scores.reduce((a, b) => a + b, 0) / st.scores.length)
                  : null;
                return `
                <div class="row row--between" style="padding:10px;border-bottom:1px solid var(--border);cursor:pointer"
                     data-student="${m.id}">
                  <div style="flex:1">
                    <strong>${escape(m.last_name || '')} ${escape(m.first_name || '')}</strong>
                    <div class="text-muted" style="font-size:var(--fs-sm)">${escape(m.email || '')}</div>
                  </div>
                  <div class="row" style="gap:var(--space-2)">
                    ${avg != null
                      ? `<span class="badge">ср. балл: <strong class="text-accent">&nbsp;${avg}</strong></span>`
                      : `<span class="badge">ср. балл: —</span>`}
                    <span class="badge">${done}/${tasks.length} заданий</span>
                    <button class="btn btn--danger btn--sm" data-remove="${m.id}">Удалить</button>
                  </div>
                </div>`;
              }).join('')}
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
      btn.addEventListener('click', async (e) => {
        e.stopPropagation();
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

    document.querySelectorAll('[data-student]').forEach(row => {
      row.addEventListener('click', () => {
        const sid = Number(row.getAttribute('data-student'));
        openStudentModal(id, sid, members, tasks, subsByTask);
      });
    });

    document.getElementById('add-student')?.addEventListener('click', () => openAddStudentModal(id));
  } catch (err) {
    toast(err.message, 'error');
    renderLayout(`<div class="empty"><div class="empty__title">Группа не найдена</div></div>`);
  }
}

function openStudentModal(groupId, studentId, members, tasks, subsByTask) {
  const m = members.find(x => x.id === studentId);
  if (!m) return;

  const rows = [];
  tasks.forEach((t, i) => {
    (subsByTask[i] || []).forEach(s => {
      if (s.student_id === studentId) rows.push({ task: t, sub: s });
    });
  });

  openModal({
    title: `${m.last_name || ''} ${m.first_name || ''} — работы`,
    body: rows.length === 0
      ? `<p class="text-muted">Студент ещё не сдал ни одного задания в этой группе.</p>`
      : `<div class="stack stack--sm">
          ${rows.map(({ task, sub }) => `
            <a class="card card--interactive" href="#/submissions/${sub.id}" style="padding:var(--space-3)">
              <div class="row row--between">
                <div>
                  <strong>${escape(task.title)}</strong>
                  <div class="text-muted" style="font-size:var(--fs-sm)">
                    сдано ${formatDateTime(sub.submitted_at || sub.created_at)}
                  </div>
                </div>
                <div class="row" style="gap:var(--space-2)">
                  <span class="badge badge--${statusClass(sub.status)}">${statusLabel(sub.status)}</span>
                  <span class="text-muted">AI: ${sub.ai_score ?? '—'}</span>
                  ${sub.final_score != null
                    ? `<strong class="score score--${scoreClass(sub.final_score)}"><span class="score__value">${sub.final_score}</span></strong>`
                    : ''}
                </div>
              </div>
            </a>
          `).join('')}
        </div>`,
    footer: `<button class="btn btn--ghost" data-cancel>Закрыть</button>`,
  });
  const backdrop = document.querySelector('.modal-backdrop');
  backdrop.querySelector('[data-cancel]').addEventListener('click', () => backdrop.remove());
}

function openAddStudentModal(groupId) {
  const { close } = openModal({
    title: 'Добавить студента',
    body: `
      <div style="display:flex;gap:var(--space-2);margin-bottom:var(--space-4)">
        <button class="btn btn--primary btn--sm tab-btn" data-tab="existing">Существующий аккаунт</button>
        <button class="btn btn--ghost btn--sm tab-btn" data-tab="new">Создать новый</button>
      </div>

      <form id="add-student-form" class="stack">
        <div id="tab-existing" class="tab-content">
          <div class="field">
            <label class="field__label">Email студента</label>
            <input class="input" type="email" name="email" placeholder="student@example.com" />
            <div class="field__hint">Введите email зарегистрированного студента</div>
          </div>
        </div>

        <div id="tab-new" class="tab-content" style="display:none">
          <div class="field">
            <label class="field__label">Имя</label>
            <input class="input" name="first_name" placeholder="Иван" />
          </div>
          <div class="field">
            <label class="field__label">Фамилия</label>
            <input class="input" name="last_name" placeholder="Иванов" />
          </div>
          <div class="field">
            <label class="field__label">Email</label>
            <input class="input" type="email" name="email_new" placeholder="ivan@example.com" />
          </div>
          <div class="field">
            <label class="field__label">Пароль (временный)</label>
            <input class="input" type="password" name="password" minlength="8" placeholder="Минимум 8 символов" />
          </div>
        </div>
      </form>
    `,
    footer: `
      <button class="btn btn--ghost" data-cancel>Отмена</button>
      <button class="btn btn--primary" data-submit>Добавить</button>
    `,
  });

  const backdrop = document.querySelector('.modal-backdrop');
  let activeTab = 'existing';

  backdrop.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      activeTab = btn.dataset.tab;
      backdrop.querySelectorAll('.tab-btn').forEach(b => {
        b.className = b.className.replace('btn--primary', 'btn--ghost');
      });
      btn.className = btn.className.replace('btn--ghost', 'btn--primary');
      backdrop.querySelector('#tab-existing').style.display = activeTab === 'existing' ? 'block' : 'none';
      backdrop.querySelector('#tab-new').style.display = activeTab === 'new' ? 'block' : 'none';
    });
  });

  backdrop.querySelector('[data-cancel]').addEventListener('click', close);
  backdrop.querySelector('[data-submit]').addEventListener('click', async () => {
    const form = document.getElementById('add-student-form');
    const data = readForm(form);

    let payload;
    if (activeTab === 'existing') {
      if (!data.email) { toast('Укажите email студента', 'warning'); return; }
      payload = { email: data.email };
    } else {
      if (!data.first_name || !data.last_name || !data.email_new || !data.password) {
        toast('Заполните все поля', 'warning'); return;
      }
      payload = {
        email: data.email_new,
        first_name: data.first_name,
        last_name: data.last_name,
        password: data.password,
      };
    }

    try {
      await api.groups.addMember(groupId, payload);
      toast('Студент добавлен в группу', 'success');
      close();
      renderGroupDetail({ id: groupId });
    } catch (err) {
      toast(err.message, 'error');
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