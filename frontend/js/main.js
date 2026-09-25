import { route, setNotFound, startRouter, navigate } from './core/router.js';
import { restoreSession } from './core/auth.js';
import { store } from './core/store.js';
import { initTheme } from './core/theme.js';

import { renderLogin } from './pages/login.js';
import { renderRegister } from './pages/register.js';
import { renderTeacherDashboard } from './pages/teacher-dashboard.js';
import { renderStudentDashboard } from './pages/student-dashboard.js';
import { renderGroups } from './pages/groups.js';
import { renderGroupDetail } from './pages/group-detail.js';
import { renderTasks } from './pages/tasks.js';
import { renderTaskDetail } from './pages/task-detail.js';
import { renderSubmissions } from './pages/submissions.js';
import { renderSubmissionDetail } from './pages/submission-detail.js';
import { renderLayout } from './core/layout.js';
import { html } from './ui/render.js';

/* ---------- Routes ---------- */
route('/login', () => renderLogin());
route('/register', () => renderRegister());

route('/', () => {
  if (!store.state.user) return navigate('/login');
  return store.state.user.role === 'teacher'
    ? renderTeacherDashboard()
    : renderStudentDashboard();
});

route('/groups', () => {
  if (store.state.user?.role !== 'teacher') return navigate('/');
  return renderGroups();
});

route('/groups/:id', ({ id }) => {
  if (store.state.user?.role !== 'teacher') return navigate('/');
  return renderGroupDetail({ id });
});

route('/tasks', () => {
  if (!store.state.user) return navigate('/login');
  return renderTasks();
});

route('/tasks/:id', ({ id }) => {
  if (!store.state.user) return navigate('/login');
  return renderTaskDetail({ id });
});

// ТЕПЕРЬ и студент, и препод (у препода — очередь «На проверку»)
route('/submissions', () => {
  if (!store.state.user) return navigate('/login');
  return renderSubmissions();
});

route('/submissions/:id', ({ id }) => {
  if (!store.state.user) return navigate('/login');
  return renderSubmissionDetail({ id });
});

/* ---------- Bootstrap ---------- */
async function bootstrap() {
  initTheme();
  await restoreSession();
  startRouter();
}

bootstrap();