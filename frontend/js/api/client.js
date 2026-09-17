import { CONFIG } from '../config.js';

let refreshing = null;

function getTokens() {
  return {
    access: localStorage.getItem(CONFIG.TOKEN_KEY),
    refresh: localStorage.getItem(CONFIG.REFRESH_KEY),
  };
}

export function setTokens({ access, refresh }) {
  if (access) localStorage.setItem(CONFIG.TOKEN_KEY, access);
  if (refresh) localStorage.setItem(CONFIG.REFRESH_KEY, refresh);
}

export function clearTokens() {
  localStorage.removeItem(CONFIG.TOKEN_KEY);
  localStorage.removeItem(CONFIG.REFRESH_KEY);
  localStorage.removeItem(CONFIG.USER_KEY);
}

async function tryRefresh() {
  if (refreshing) return refreshing;
  const { refresh } = getTokens();
  if (!refresh) return null;

  refreshing = (async () => {
    try {
      const res = await fetch(`${CONFIG.API_BASE}/api/v1/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refresh }),
      });
      if (!res.ok) throw new Error('refresh failed');
      const data = await res.json();
      setTokens({ access: data.access_token, refresh: data.refresh_token });
      return data.access_token;
    } catch {
      clearTokens();
      return null;
    } finally {
      refreshing = null;
    }
  })();

  return refreshing;
}

export async function request(path, { method = 'GET', body, headers = {}, auth = true, retry = true } = {}) {
  const finalHeaders = { ...headers };
  if (body && !(body instanceof FormData)) {
    finalHeaders['Content-Type'] = 'application/json';
  }

  if (auth) {
    const { access } = getTokens();
    if (access) finalHeaders['Authorization'] = `Bearer ${access}`;
  }

  const res = await fetch(`${CONFIG.API_BASE}${path}`, {
    method,
    headers: finalHeaders,
    body: body instanceof FormData ? body : body ? JSON.stringify(body) : undefined,
  });

  if (res.status === 401 && auth && retry) {
    const newToken = await tryRefresh();
    if (newToken) return request(path, { method, body, headers, auth, retry: false });
    clearTokens();
    window.dispatchEvent(new CustomEvent('educheck:logout'));
    throw new Error('Сессия истекла');
  }

  if (!res.ok) {
    let message = `Ошибка ${res.status}`;
    try {
      const data = await res.json();
      message = data.detail || data.message || message;
      if (Array.isArray(message)) message = message.map(m => m.msg || m).join(', ');
    } catch { /* ignore */ }
    const err = new Error(message);
    err.status = res.status;
    throw err;
  }

  if (res.status === 204) return null;
  const ct = res.headers.get('content-type') || '';
  return ct.includes('application/json') ? res.json() : res.text();
}