import { api } from '../api/index.js';
import { renderLayout } from '../core/layout.js';
import { html, escape, formatDateTime } from '../ui/render.js';
import { toast } from '../ui/toast.js';
import { store } from '../core/store.js';

export async function renderSubmissionDetail({ id }) {
  renderLayout(`<div class="skeleton" style="height:120px"></div>`);
  try {
    const s = await api.submissions.get(id);
    const isTeacher = store.state.user?.role === 'TEACHER';

    const content = html`
      <div class="breadcrumbs">
        <a href="#/submissions">Работы</a>
        <span class="breadcrumbs__sep">/</span>
        <span>Работа #${s.id.slice(0, 8)}</span>
      </div>

      <div class="page-header">
        <div class="page-header__title">
          <h1>Работа студента</h1>
          <p class="page-header__subtitle">Загружена ${formatDateTime(s.created_at)}</p>
        </div>
        <div class="page-header__actions">
          <span class="badge badge--${statusClass(s.status)}">${statusLabel(s.status)}</span>
          ${isTeacher ? `<button class="btn btn--secondary" id="run-ai">Запустить AI-проверку</button>` : ''}
        </div>
      </div>

      <div class="ai-review" style="margin-bottom: var(--space-6)">
        <div class="ai-review__panel">
          <h4>Текст работы</h4>
          <div class="submission-text">${escape(s.student_comment || '—')}</div>
        </div>

        <div class="ai-review__panel ai-review__panel--ai">
          <h4>AI-разбор ${s.ai_score != null ? `<span class="score score--${scoreClass(s.ai_score)}"> <span class="score__value">${s.ai_score}</span><span class="score__max">/100</span></span>` : ''}</h4>
          ${s.ai_feedback
            ? `<div class="md">${renderSafeMarkdown(s.ai_feedback)}</div>`
            : `<p class="text-muted">AI-проверка ещё не выполнена.</p>`}
        </div>
      </div>

      ${isTeacher ? renderTeacherReview(s) : ''}
    `;
    renderLayout(content);

    document.getElementById('run-ai')?.addEventListener('click', async () => {
      try {
        await api.submissions.triggerAI(id);
        toast('AI-проверка запущена', 'info');
        setTimeout(() => renderSubmissionDetail({ id }), 2500);
      } catch (err) {
        toast(err.message, 'error');
      }
    });

    document.getElementById('review-form')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const score = Number(e.target.elements.score.value);
      const feedback = e.target.elements.feedback.value;
      try {
        await api.submissions.review(id, { final_score: score, teacher_feedback: feedback });
        toast('Итоговая оценка сохранена', 'success');
        renderSubmissionDetail({ id });
      } catch (err) {
        toast(err.message, 'error');
      }
    });
  } catch (err) {
    toast(err.message, 'error');
    renderLayout(`<div class="empty"><div class="empty__title">Работа не найдена</div></div>`);
  }
}

function renderTeacherReview(s) {
  return html`
    <div class="card">
      <h4 style="margin-bottom: var(--space-4)">Итоговая оценка преподавателя</h4>
      <form id="review-form" class="stack">
        <div class="field" style="max-width:200px">
          <label class="field__label">Оценка (0–100)</label>
          <input class="input" type="number" name="score" min="0" max="100" value="${s.final_score ?? s.ai_score ?? ''}" required />
        </div>
        <div class="field">
          <label class="field__label">Комментарий</label>
          <textarea class="textarea" name="feedback" rows="4" placeholder="Ваши замечания студенту">${escape(s.teacher_feedback || '')}</textarea>
        </div>
        <div>
          <button class="btn btn--primary" type="submit">Сохранить оценку</button>
        </div>
      </form>
    </div>
  `;
}

function statusClass(s) {
  return ({ DRAFT: 'draft', SUBMITTED: 'submitted', CHECKING: 'checking', CHECKED: 'checked', REVIEWED: 'reviewed', FAILED: 'failed' })[s] || 'draft';
}
function statusLabel(s) {
  return ({ DRAFT: 'Черновик', SUBMITTED: 'Сдано', CHECKING: 'AI проверяет', CHECKED: 'AI проверено', REVIEWED: 'Проверено', FAILED: 'Ошибка AI' })[s] || s;
}
function scoreClass(v) {
  if (v >= 75) return 'good';
  if (v >= 50) return 'warn';
  return 'bad';
}

/** Минимальный безопасный рендер markdown: экранируем HTML, потом применяем простые замены */
function renderSafeMarkdown(text) {
  let safe = escape(text);
  safe = safe.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  safe = safe.replace(/^### (.+)$/gm, '<h4>$1</h4>');
  safe = safe.replace(/^## (.+)$/gm, '<h3>$1</h3>');
  safe = safe.replace(/^\- (.+)$/gm, '<li>$1</li>');
  safe = safe.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>');
  safe = safe.replace(/\n{2,}/g, '</p><p>');
  return `<p>${safe}</p>`;
}