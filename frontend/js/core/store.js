function createStore(initial = {}) {
  const listeners = new Set();
  const state = new Proxy(initial, {
    set(target, key, value) {
      if (target[key] === value) return true;
      target[key] = value;
      listeners.forEach(fn => fn(key, value, target));
      return true;
    },
  });
  return {
    state,
    subscribe(fn) { listeners.add(fn); return () => listeners.delete(fn); },
    set(patch) { Object.assign(state, patch); },
  };
}

export const store = createStore({
  user: null,
  groups: [],
  tasks: [],
  submissions: [],
  loading: false,
});