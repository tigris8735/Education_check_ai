const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';

// Адрес бэкенда подставляется при сборке на Render (см. INSTRUCTION.md).
// Локально — localhost:8000.
const OVERRIDE = (window.__EDUCHECK_API__ || '').trim();

export const CONFIG = {
  API_BASE: OVERRIDE || (isLocal ? 'http://localhost:8000' : 'https://education-check-ai.onrender.com'),
  TOKEN_KEY: 'educheck.access',
  REFRESH_KEY: 'educheck.refresh',
  USER_KEY: 'educheck.user',
};