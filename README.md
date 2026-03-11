Приложение позволяет:

- Регистрация и авторизация пользователей по email и паролю  
- Создание команды (компании): админ создаёт, приглашает участников  
- Роли: админ, менеджер, сотрудник  
- Задачи: создание, назначение исполнителя, статусы (открыто, в работе, выполнено), комментарии  
- Оценка работы: менеджер ставит оценку от 1 до 5 за выполненную задачу  
- Встречи: назначение времени, выбор участников, проверка пересечений  
- Календарь: единый обзор задач (по дедлайну) и встреч (по времени) в виде месячной таблицы  
- Админ-панель: управление всеми сущностями через /admin (на базе SQLAdmin)  
- HTML-интерфейс: полноценный веб-фронтенд без необходимости использовать API напрямую

Установка и запуск:

Требования:

- Python 3.12
- pip

Шаги:

1. Клонируйте репозиторий:

       git clone <ваш репозиторий>
       cd <папка-проекта>

2. Создайте виртуальное окружение:

       python -m venv venv
       source venv/bin/activate  # Linux/Mac
       venv\Scripts\activate     # Windows

3. Установите зависимости:

       pip install -r requirements.txt

4. Настройте переменные окружения:

Создайте файл .env в корне проекта:

    DATABASE_URL=sqlite+aiosqlite:///./business.db
    SECRET_KEY=your-very-long-secret-key-here
    ALGORITHM=HS256
    ACCESS_TOKEN_EXPIRE_MINUTES=30

5. Запустите сервер:

       uvicorn backend.main:app --reload

6. Откройте в браузере:

       Веб-интерфейс: http://127.0.0.1:8000
       Документация API (Swagger): http://127.0.0.1:8000/docs
       Админ-панель: http://127.0.0.1:8000/admin

Запуск в докере:

1. Соберите и запустите контейнеры
docker-compose up --build

2. Приложение будет доступно по адресу:
http://localhost:8000

  Структура проекта:

     management_system/
     ├── backend/                    # Основной код приложения
     │   ├── __init__.py
     │   ├── main.py                 # Точка входа
     │   ├── core/                   # Конфигурация и безопасность
     │   │   ├── __init__.py
     │   │   ├── config.py
     │   │   └── security.py
     |   |   |__config_test.py
     │   ├── db/                     # Сессия БД
     │   │   ├── __init__.py
     │   │   └── session.py
     │   ├── models/                 # SQLAlchemy модели
     │   │   ├── __init__.py
     │   │   ├── base.py
     │   │   ├── user.py
     │   │   ├── team.py
     │   │   ├── task.py
     │   │   ├── meeting.py
     │   │   ├── evaluation.py
     │   │   └── comment.py
     │   ├── schemas/                # Pydantic схемы
     │   │   ├── __init__.py
     │   │   ├── auth.py
     │   │   ├── user.py
     │   │   ├── team.py
     │   │   ├── task.py
     │   │   ├── meeting.py
     │   │   └── evaluation.py
     |   |   |__ event_calendar.py
     │   ├── crud/                   # Логика работы с БД
     │   │   ├── __init__.py
     │   │   ├── user.py
     │   │   ├── team.py
     │   │   ├── task.py
     │   │   ├── meeting.py
     │   │   ├── evaluation.py
     │   │   └── event_calendar.py
     │   ├── api/                     # API и HTML роутеры
     │   │    ├── __init__.py   
     │   │    ├── auth.py
     │   │    ├── team.py
     │   │    ├── task.py
     │   │    ├── evaluation.py
     │   │    ├── meeting.py
     │   │    └── html_views.py
     |   |    |__ event_calendar.py
     |   |    |__ deps.py
     │   ├── middleware/             # Middleware
     │   │   ├── __init__.py
     │   │   ├── auth_middleware.py
     │   ├── admin.py                # Админ-панель (SQLAdmin)
     │   └── templates/              # Jinja2 шаблоны
     │       ├── base.html
     │       ├── auth/
     │       │   ├── login.html
     │       │   └── register.html
     │       ├── dashboard.html
     │       ├── calendar.html
     │       ├── tasks.html
     │       ├── task_create.html
     │       ├── meetings.html
     │       ├── meeting_create.html
     │       ├── evaluation_create.html
     │       ├── profile_edit.html
     │       ├── profile_delete.html
     │       └── join_team.html
     |--tests/
         |-- conftest.py
         |-- test_auth.py
         |-- test_task.py
         |__ test_team.py
     ├── data/                       # SQLite БД (игнорируется в .gitignore)
     ├── Dockerfile
     ├── docker-compose.yml
     ├── .env.example
     ├── .dockerignore
     ├── requirements.txt
     └── README.md

Примеры использования
1. Регистрация и вход:

Через браузер:

       Перейдите на http://localhost:8000/register
       Заполните форму: email, пароль, имя
       Нажмите «Register» → автоматический вход

    Через API:

       curl -X POST http://localhost:8000/api/auth/register \
       -H "Content-Type: application/json" \
       -d '{
       "email": "user@example.com",
       "password": "secure123",
       "full_name": "Иван Петров"
       }'
2. Создание команды:

Через интерфейс:

    Войдите в систему
    Перейдите в /dashboard
    Нажмите «Создать команду» (или используйте API)
    Вы автоматически становитесь админом команды
    Скопируйте invite code и отправьте коллегам

Через интерфейс (для коллег):

    Перейдите в /join
    Введите invite code
    Вы присоединяетесь к команде с ролью user

3. Создание задачи:

Через интерфейс:

        Перейдите в /tasks
        Нажмите «+ Create New Task»
        Заполните форму:
            Название
            Описание (опционально)
            Дедлайн (опционально)
            Исполнитель (выберите из команды)
        Нажмите «Create Task»

Исполнитель:

    Открывает /tasks
    Видит назначенную задачу со статусом open
    Нажимает «Start Work» → статус меняется на in_progress
    После завершения нажимает «Mark as Done» → статус done

Менеджер:

    Видит задачу со статусом done
    Нажимает «Evaluate»
    Выбирает оценку от 1 до 5
    Отправляет → оценка сохраняется

4. Создание встречи:

Через интерфейс:

    Перейдите в /meetings
    Нажмите «+ Create New Meeting»
    Заполните форму:
        Название
        Время начала и окончания
        Участники (отметьте галочками)
    Нажмите «Create Meeting»

5. Просмотр календаря:

        Перейдите в /calendar
        Увидите месячную таблицу:
            Встречи — жёлтый фон
            Задачи с дедлайном — голубой фон
            Сегодняшний день — подсвечен
        Нажмите «Prev» / «Next» для навигации по месяцам

6. Обновление профиля:

       Перейдите в /profile/edit
       Измените имя или email
       Нажмите «Save Changes»

7. Удаление аккаунта:

       Перейдите в /profile/delete
       Нажмите «Delete My Account»
       Подтвердите действие

Примеры запросов и ответов (API):

Регистрация:

  Запрос:

    POST /api/auth/register
    Content-Type: application/json

    {
    "email": "user@example.com",
    "password": "secure123",
    "full_name": "Николай Стужа"
    }

  Ответ:

    {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
    }

Вход:

  Запрос:

    POST /api/auth/login
    Content-Type: application/x-www-form-urlencoded

    username=user@example.com&password=secure123

  Ответ:
    
    {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
    }

Создание задачи:

  Запрос:

    POST /api/tasks/
    Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    Content-Type: application/json

    {
      "title": "Подготовить отчёт",
      "description": "Ежемесячный финансовый отчёт за март",
      "deadline": "2026-03-15T18:00:00",
      "assignee_id": 2
    }

  Ответ:

      {
    "id": 1,
    "title": "Подготовить отчёт",
    "description": "Ежемесячный финансовый отчёт за март",
    "status": "open",
    "deadline": "2026-03-15T18:00:00",
    "creator": {
      "id": 1,
      "email": "admin@example.com",
      "full_name": "Админ",
      "role": "admin"
      },
    "assignee": {
      "id": 2,
      "email": "user@example.com",
      "full_name": "Иван Петров",
      "role": "user"
      },
    "comments": []
      }

Получение календаря за день:

  Запрос:

    GET /api/calendar/day?day=2026-03-10
    Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

  Ответ:

    {
    "date": "2026-03-10",
    "events": [
    {
      "id": 1,
      "title": "Встреча: Планирование",
      "type": "meeting",
      "start": "2026-03-10T10:00:00",
      "end": "2026-03-10T11:00:00",
      "creator_id": 1
    },
    {
      "id": 2,
      "title": "Задача: Фикс бага",
      "type": "task",
      "start": "2026-03-10T15:00:00",
      "end": "2026-03-10T15:00:00",
      "assignee_id": 2,
      "creator_id": 1
    }
    ]
    }

Оценка задачи:
  
  Запрос:
    
    POST /api/evaluations/
    Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    Content-Type: application/json

    {
    "task_id": 1,
    "score": 5
    }

  Ответ:

    {
    "id": 1,
    "task_id": 1,
    "score": 5,
    "evaluator_id": 1,
    "evaluated_user_id": 2,
    "created_at": "2026-03-10T16:30:00"
    }

Переменные окружения:

  Создайте файл .env на основе .env.example:
    
    # База данных (SQLite для MVP)
    DATABASE_URL=sqlite+aiosqlite:///./data/business.db
    # JWT-конфигурация
    SECRET_KEY=your-super-secret-key-here
    ALGORITHM=HS256
    ACCESS_TOKEN_EXPIRE_MINUTES=30

Документация:

    Swagger: http://localhost:8000/docs
    ReDoc: http://localhost:8000/redoc
    Админ-панель: http://localhost:8000/admin

Тестирование:

    # Запуск тестов
    pytest -v

Технологии:

      - Backend: FastAPI 
      - База данных: SQLite 
      - ORM: SQLAlchemy 
      - Аутентификация: JWT + HTTP-only cookies
      - Фронтенд: Jinja2 
      - Админка: SQLAdmin
      - Тестирование: pytest + httpx


