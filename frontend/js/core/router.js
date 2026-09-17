const routes = [];
let notFoundHandler = () => {};

export function route(pattern, handler) {
  const keys = [];
  const regex = new RegExp(
    '^' + pattern.replace(/:([^/]+)/g, (_, k) => { keys.push(k); return '([^/]+)'; }) + '$'
  );
  routes.push({ regex, keys, handler });
}

export function setNotFound(fn) { notFoundHandler = fn; }

function parseHash() {
  const hash = location.hash.replace(/^#/, '') || '/';
  return hash.startsWith('/') ? hash : '/' + hash;
}

export function navigate(path) {
  if (location.hash === '#' + path) return;
  location.hash = path;
}

export async function resolve() {
  const path = parseHash();
  for (const r of routes) {
    const m = path.match(r.regex);
    if (m) {
      const params = {};
      r.keys.forEach((k, i) => params[k] = decodeURIComponent(m[i + 1]));
      await r.handler(params);
      window.scrollTo(0, 0);
      return;
    }
  }
  notFoundHandler();
}

export function startRouter() {
  window.addEventListener('hashchange', resolve);
  resolve();
}