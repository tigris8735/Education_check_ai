const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';

export const CONFIG = {
  // Если мы локально - берем 8000, иначе подставляем URL вашего задеплоенного бэка
  // Замените 'https://ВАШ-БЭК-СЕРВИС.onrender.com' на реальный URL вашего Web Service
  API_BASE: window.__EDUCHECK_API__ || (isLocal ? 'http://localhost:8000' : 'https://educheck-api.onrender.com'),
  TOKEN_KEY: 'educheck.access',
  REFRESH_KEY: 'educheck.refresh',
  USER_KEY: 'educheck.user',
};