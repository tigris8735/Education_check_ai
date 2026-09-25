const THEME_KEY = 'educheck.theme';

export function getStoredTheme() {
  try {
    return localStorage.getItem(THEME_KEY) || 'light';
  } catch { return 'light'; }
}

export function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem(THEME_KEY, theme);
}

export function toggleTheme() {
  const current = getStoredTheme();
  const next = current === 'dark' ? 'light' : 'dark';
  applyTheme(next);
  return next;
}

export function initTheme() {
  applyTheme(getStoredTheme());
}