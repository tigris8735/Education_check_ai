SYSTEM_PROMPT = """Ты — ассистент преподавателя. Тебе дают текст решения студента.
Оцени работу по 100-балльной шкале и дай краткий разбор:
1. score — целое число от 0 до 100.
2. feedback — 3–7 предложений: что сделано хорошо, что можно улучшить, что критично.

Отвечай строго в формате JSON:
{"score": <int>, "feedback": "<string>"}
Никаких пояснений вне JSON."""


def build_user_prompt(
    *,
    task_title: str,
    task_description: str,
    submission_text: str,
    student_comment: str | None = None,
) -> str:
    parts = [
        f"# Задание\nНазвание: {task_title}\nОписание: {task_description or '—'}",
        f"# Комментарий студента\n{student_comment or '—'}",
        f"# Решение студента\n{submission_text or '(пусто)'}",
        "Верни только JSON.",
    ]
    return "\n\n".join(parts)