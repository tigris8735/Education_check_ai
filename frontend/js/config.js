const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';

export const CONFIG = {
  // Реальный продакшен-бэкенд на Render
  API_BASE: isLocal ? 'http://localhost:8000' : 'https://education-check-ai.onrender.com',
  TOKEN_KEY: 'educheck.access',
  REFRESH_KEY: 'educheck.refresh',
  USER_KEY: 'educheck.user',
};