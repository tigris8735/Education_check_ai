export function readForm(form) {
  const data = {};
  new FormData(form).forEach((v, k) => { data[k] = v; });
  return data;
}

export function setError(form, name, message) {
  const input = form.elements[name];
  if (!input) return;
  input.classList.add('is-error');
  let err = input.parentElement.querySelector('.field__error');
  if (!err) {
    err = document.createElement('div');
    err.className = 'field__error';
    input.parentElement.appendChild(err);
  }
  err.textContent = message;
}

export function clearErrors(form) {
  form.querySelectorAll('.is-error').forEach(el => el.classList.remove('is-error'));
  form.querySelectorAll('.field__error').forEach(el => el.remove());
}