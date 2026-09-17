export function toast(message, type = 'info', timeout = 4000) {
  const root = document.getElementById('toast-root');
  const el = document.createElement('div');
  el.className = `toast toast--${type}`;
  el.innerHTML = `
    <div style="flex:1">${message}</div>
    <button class="toast__close" aria-label="Закрыть">×</button>
  `;
  const close = () => el.remove();
  el.querySelector('.toast__close').addEventListener('click', close);
  root.appendChild(el);
  if (timeout) setTimeout(close, timeout);
}