import { request } from './client.js';

export const api = {
  auth: {
    register: (payload) => request('/api/v1/auth/register', { method: 'POST', body: payload, auth: false }),
    login:    (payload) => request('/api/v1/auth/login',    { method: 'POST', body: payload, auth: false }),
    me:       ()        => request('/api/v1/users/me'),
  },
  users: {
    list:   ()     => request('/api/v1/users'),
    get:    (id)   => request(`/api/v1/users/${id}`),
  },
  groups: {
    list:    ()           => request('/api/v1/groups'),
    get:     (id)         => request(`/api/v1/groups/${id}`),
    create:  (payload)    => request('/api/v1/groups', { method: 'POST', body: payload }),
    update:  (id, p)      => request(`/api/v1/groups/${id}`, { method: 'PATCH', body: p }),
    remove:  (id)         => request(`/api/v1/groups/${id}`, { method: 'DELETE' }),
    addMember:    (id, sid) => request(`/api/v1/groups/${id}/members`, { method: 'POST', body: { student_id: sid } }),
    removeMember: (id, sid) => request(`/api/v1/groups/${id}/members/${sid}`, { method: 'DELETE' }),
  },
  tasks: {
    list:    ()        => request('/api/v1/tasks'),
    get:     (id)      => request(`/api/v1/tasks/${id}`),
    create:  (payload) => request('/api/v1/tasks', { method: 'POST', body: payload }),
    update:  (id, p)   => request(`/api/v1/tasks/${id}`, { method: 'PATCH', body: p }),
    remove:  (id)      => request(`/api/v1/tasks/${id}`, { method: 'DELETE' }),
    listByGroup: (gid) => request(`/api/v1/tasks?group_id=${gid}`),
  },
  submissions: {
    list:    (params = {}) => {
      const q = new URLSearchParams(params).toString();
      return request(`/api/v1/submissions${q ? '?' + q : ''}`);
    },
    get:     (id)         => request(`/api/v1/submissions/${id}`),
    create:  (payload)    => request('/api/v1/submissions', { method: 'POST', body: payload }),
    update:  (id, p)      => request(`/api/v1/submissions/${id}`, { method: 'PATCH', body: p }),
    review:  (id, payload) => request(`/api/v1/submissions/${id}/review`, { method: 'POST', body: payload }),
    triggerAI: (id)       => request(`/api/v1/submissions/${id}/check`, { method: 'POST' }),
    listByTask: (tid)     => request(`/api/v1/submissions?task_id=${tid}`),
  },
};