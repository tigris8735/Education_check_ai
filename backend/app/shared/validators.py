import re

# Группа вида "15ИС", "21ПИ", "20ИС" и т.п.
GROUP_NAME_RE = re.compile(r"^\d{2}[А-ЯA-Z]{2,4}$")

# Простая проверка e-mail, чтобы не тянуть pydantic[email]
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_group_name(value: str) -> str:
    value = value.strip().upper()
    if not GROUP_NAME_RE.match(value):
        raise ValueError("Некорректное название группы. Формат: 15ИС, 21ПИ и т.п.")
    return value


def validate_email(value: str) -> str:
    value = value.strip().lower()
    if not EMAIL_RE.match(value):
        raise ValueError("Некорректный e-mail")
    return value


def validate_password(value: str) -> str:
    if len(value) < 8:
        raise ValueError("Пароль должен содержать минимум 8 символов")
    if len(value) > 128:
        raise ValueError("Пароль слишком длинный")
    return value