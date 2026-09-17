import { api } from '../api/index.js';
import { setTokens, clearTokens } from '../api/client.js';
import { CONFIG } from '../config.js';
import { store } from './store.js';

export function getStoredUser() {
  try { return JSON.parse(localStorage.getItem(CONFIG.USER_KEY) || 'null'); }
  catch { return null; }
}

export function setStoredUser(user) {
  if (user) localStorage.setItem(CONFIG.USER_KEY, JSON.stringify(user));
  else localStorage.removeItem(CONFIG.USER_KEY);
}

export async function login(email, password) {
  const data = await api.auth.login({ email, password });
  setTokens({ access: data.access_token, refresh: data.refresh_token });
  const me = data.user || await api.auth.me();
  setStoredUser(me);
  store.set({ user: me });
  return me;
}

export async function register(payload) {
  const data = await api.auth.register(payload);
  if (data?.access_token) {
    setTokens({ access: data.access_token, refresh: data.refresh_token });
    const me = data.user || await api.auth.me();
    setStoredUser(me);
    store.set({ user: me });
  }
  return data;
}

export async function restoreSession() {
  const user = getStoredUser();
  if (!user) return null;
  try {
    const fresh = await api.auth.me();
    setStoredUser(fresh);
    store.set({ user: fresh });
    return fresh;
  } catch {
    logout();
    return null;
  }
}

export function logout() {
  clearTokens();
  setStoredUser(null);
  store.set({ user: null });
  location.hash = '#/login';
}

export function isTeacher() { return store.state.user?.role === 'TEACHER'; }
export function isStudent() { return store.state.user?.role === 'STUDENT'; }