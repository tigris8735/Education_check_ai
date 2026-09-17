export function openModal({ title = '', body = '', footer = '', size = '' } = {}) {
  const root = document.getElementById('modal-root');
  const backdrop = document.createElement('div');
  backdrop.className = 'modal-backdrop';
  backdrop.innerHTML = `
    <div class="modal ${size === 'lg' ? 'modal--lg' : ''}" role="dialog" aria-modal="true">
      <div class="modal__header">
        <div class="modal__title">${title}</div>
        <button class="btn btn--ghost btn--sm" data-close aria-label="Закрыть">✕</button>
      </div>
      <div class="modal__body">${body}</div>
      ${footer ? `<div class="modal__footer">${footer}</div>` : ''}
    </div>
  `;
  const close = () => backdrop.remove();
  backdrop.addEventListener('click', (e) => { if (e.target === backdrop) close(); });
  backdrop.querySelector('[data-close]').addEventListener('click', close);
  document.addEventListener('keydown', function esc(e) {
    if (e.key === 'Escape') { close(); document.removeEventListener('keydown', esc); }
  });
  root.appendChild(backdrop);
  return { el: backdrop, close };
}