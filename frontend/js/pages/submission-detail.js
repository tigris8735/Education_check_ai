import { api } from '../api/index.js';
import { renderLayout } from '../core/layout.js';
import { html, escape, formatDateTime } from '../ui/render.js';
import { toast } from '../ui/toast.js';
import { store } from '../core/store.js';

export async function renderSubmissionDetail({ id }) {
  renderLayout(`<div class="skeleton" style="height:120px"></div>`);
  try {
    const s = await api.submissions.get(id);
    const isTeacher = store.state.user?.role === 'teacher';
    const hasVerdict = s.final_score != null || (s.teacher_feedback || '').trim().length > 0;

    const content = html`
      <div class="breadcrumbs">
        <a href="#/">Главная</a>
        <span class="breadcrumbs__sep">/</span>
        <span>Работа #${s.id}</span>
      </div>

      <div class="page-header">
        <div class="page-header__title">
          <h1>${escape(s.student_last_name || '')} ${escape(s.student_first_name || '')}</h1>
          <p class="page-header__subtitle">
            ${escape(s.task_title || 'Задание #' + s.task_id)} · ${escape(s.student_group_name || '')} ·
            сдана ${formatDateTime(s.submitted_at || s.created_at)}
          </p>
        </div>
        <div class="page-header__actions">
          <span class="badge badge--${statusClass(s.status)}">${statusLabel(s.status)}</span>
          ${isTeacher ? `<button class="btn btn--secondary" id="run-ai">🤖 Запустить AI-проверку</button>` : ''}
        </div>
      </div>

      <div class="ai-review" style="margin-bottom: var(--space-6)">
        <div class="ai-review__panel">
          <h4>Текст работы</h4>
          <div class="submission-text">${escape(s.student_comment || '—')}</div>
        </div>

        <div class="ai-review__panel ai-review__panel--ai">
          <h4>AI-разбор ${s.ai_score != null
            ? `<span class="score"><span class="score__value">${s.ai_score}</span><span class="score__max">/100</span></span>`
            : ''}</h4>
          ${s.ai_status === 'error'
            ? `<p style="color:var(--danger)">❌ Ошибка AI: ${escape(s.ai_error || 'неизвестная')}</p>`
            : s.ai_feedback
              ? `<div class="md">${renderSafeMarkdown(s.ai_feedback)}</div>`
              : `<p class="text-muted">AI-проверка ещё не выполнена.</p>`}
        </div>
      </div>

      ${!isTeacher && hasVerdict ? teacherVerdictCard(s) : ''}

      ${(s.files?.length ?? 0) > 0 ? `
        <div class="card" style="margin-bottom: var(--space-6)">
          <h4 style="margin-bottom: var(--space-3)">Файлы работы (${s.files.length})</h4>
          <div class="stack stack--sm">
            ${s.files.map(f => `
              <div class="row row--between">
                <div>📄 ${escape(f.original_name)}
                  <span class="text-muted" style="font-size:var(--fs-sm)">(${(f.size / 1024).toFixed(1)} KB)</span>
                </div>
                <button class="btn btn--secondary btn--sm" data-download="${f.id}">Скачать</button>
              </div>
            `).join('')}
          </div>
        </div>` : ''}

      ${isTeacher ? renderTeacherReview(s) : ''}
    `;

    renderLayout(content);

    document.querySelectorAll('[data-download]').forEach(btn => {
      btn.addEventListener('click', async () => {
        try {
          const { url } = await api.files.downloadUrl(btn.getAttribute('data-download'));
          window.open(url, '_blank');
        } catch (e) { toast(e.message, 'error'); }
      });
    });

    document.getElementById('run-ai')?.addEventListener('click', async () => {
      const btn = document.getElementById('run-ai');
      btn.disabled = true;
      btn.textContent = '⏳ Проверка выполняется...';
      try {
        const check = await api.submissions.triggerAI(id, { force: true });
        if (check?.status === 'error') {
          toast(`Ошибка AI: ${check.error || 'см. панель проверки'}`, 'error');
          renderSubmissionDetail({ id });
          return;
        }
        toast('AI-проверка запущена...', 'info');
        let attempts = 0;
        const poll = setInterval(async () => {
          attempts++;
          try {
            const fresh = await api.submissions.get(id);
            if (['done', 'error'].includes(fresh.ai_status) || attempts > 30) {
              clearInterval(poll);
              renderSubmissionDetail({ id });
            }
          } catch { clearInterval(poll); }
        }, 2000);
      } catch (err) {
        btn.disabled = false;
        btn.textContent = '🤖 Запустить AI-проверку';
        toast(err.message, 'error');
      }
    });

    document.getElementById('review-form')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const score = Number(e.target.elements.score.value);
      const feedback = e.target.elements.feedback.value;
      try {
        await api.submissions.updateFinalScore(id, { final_score: score, teacher_feedback: feedback });
        toast('Итоговая оценка сохранена', 'success');
        renderSubmissionDetail({ id });
      } catch (err) { toast(err.message, 'error'); }
    });
  } catch (err) {
    toast(err.message, 'error');
    renderLayout(`<div class="empty"><div class="empty__title">Работа не найдена</div></div>`);
  }
}

/* Карточка вердикта препода для СТУДЕНТА */
function teacherVerdictCard(s) {
  return html`
    <div class="card verdict-card" style="margin-bottom: var(--space-6)">
      <h4 style="margin-bottom: var(--space-3)">Оценка и комментарий преподавателя</h4>
      ${s.final_score != null ? `
        <div style="margin-bottom: var(--space-3)">
          <span class="score score--${scoreClass(s.final_score)}">
            <span class="score__value">${s.final_score}</span><span class="score__max">/100</span>
          </span>
        </div>` : ''}
      ${s.teacher_feedback
        ? `<div class="submission-text">${escape(s.teacher_feedback)}</div>`
        : `<p class="text-muted">Комментарий не оставлен</p>`}
    </div>
  `;
}

function renderTeacherReview(s) {
  return html`
    <div class="card">
      <h4 style="margin-bottom: var(--space-4)">Итоговая оценка преподавателя</h4>
      <form id="review-form" class="stack">
        <div class="field" style="max-width:200px">
          <label class="field__label">Оценка (0–100)</label>
          <input class="input" type="number" name="score" min="0" max="100"
                 value="${s.final_score ?? s.ai_score ?? ''}" required />
        </div>
        <div class="field">
          <label class="field__label">Комментарий</label>
          <textarea class="textarea" name="feedback" rows="4"
                    placeholder="Ваши замечания студенту">${escape(s.teacher_feedback || '')}</textarea>
        </div>
        <div><button class="btn btn--primary" type="submit">Сохранить оценку</button></div>
      </form>
    </div>
  `;
}

function statusClass(s) {
  return ({ draft: 'draft', submitted: 'submitted', checking: 'checking',
            checked: 'checked', reviewed: 'reviewed', failed: 'failed' })[s] || 'draft';
}

function statusLabel(s) {
  return ({ draft: 'Черновик', submitted: 'Сдано', checking: 'AI проверяет',
            checked: 'AI проверено', reviewed: 'Оценено преподом', failed: 'Ошибка AI' })[s] || s;
}

function scoreClass(v) {
  if (v >= 75) return 'good';
  if (v >= 50) return 'warn';
  return 'bad';
}

function renderSafeMarkdown(text) {
  let safe = escape(text);
  safe = safe.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  safe = safe.replace(/^### (.+)$/gm, '<h4>$1</h4>');
  safe = safe.replace(/^## (.+)$/gm, '<h3>$1</h3>');
  safe = safe.replace(/^- (.+)$/gm, '<li>$1</li>');
  safe = safe.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>');
  safe = safe.replace(/\n{2,}/g, '</p><p>');
  return `<p>${safe}</p>`;
}