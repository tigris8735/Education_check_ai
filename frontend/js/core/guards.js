import { store } from './store.js';
import { navigate } from './router.js';

export function requireAuth() {
  if (!store.state.user) {
    navigate('/login');
    return false;
  }
  return true;
}

export function requireRole(...roles) {
  if (!requireAuth()) return false;
  if (!roles.includes(store.state.user.role)) {
    navigate('/');
    return false;
  }
  return true;
}