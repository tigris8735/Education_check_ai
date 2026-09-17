const app = () => document.getElementById('app');

export function mount(html) {
  app().innerHTML = html;
  app().firstElementChild?.classList.add('fade-in');
}

export function html(strings, ...values) {
  return strings.reduce((acc, s, i) => acc + s + (values[i] ?? ''), '');
}

export function escape(str) {
  if (str == null) return '';
  return String(str)
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;').replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

export function formatDate(date) {
  if (!date) return '—';
  const d = new Date(date);
  return d.toLocaleDateString('ru-RU', { day: '2-digit', month: 'short', year: 'numeric' });
}

export function formatDateTime(date) {
  if (!date) return '—';
  const d = new Date(date);
  return d.toLocaleString('ru-RU', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

export function initials(name = '') {
  return name.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase() || '?';
}

export function relativeDeadline(date) {
  if (!date) return '';
  const d = new Date(date);
  const diff = d - new Date();
  const days = Math.round(diff / 86400000);
  if (diff < 0) return `просрочено на ${Math.abs(days)} дн.`;
  if (days === 0) return 'сегодня';
  if (days === 1) return 'завтра';
  return `через ${days} дн.`;
}