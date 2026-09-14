# План архитектуры

## 1. Общая архитектура системы

EduCheck AI построен по микросервисной архитектуре:

- **Frontend** — статический сайт на HTML/CSS/JS.
- **API Gateway** — единая точка входа.
- **Микросервисы** — Auth, Group, Assignment, AI Check.
- **База данных** — Neon PostgreSQL.
- **Деплой** — Render.

```mermaid
graph TB
    UI[Frontend HTML/CSS/JS] --> GW[API Gateway FastAPI]
    GW --> AUTH[Auth Service]
    GW --> GROUP[Group Service]
    GW --> ASSIGN[Assignment Service]
    GW --> AI[AI Check Service]
    AUTH --> DB[(Neon PostgreSQL)]
    GROUP --> DB
    ASSIGN --> DB
    AI --> LLM[LLM API]
    AI --> DB

    style UI fill:#e1f5fe
    style GW fill:#fff3e0
    style AI fill:#f3e5f5
    style DB fill:#e8f5e9