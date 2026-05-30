# Study Bot — расписание и дедлайны (Telegram)

Курсовой проект по функциональному программированию: Telegram-бот для учебного расписания и дедлайнов с **отдельным функциональным ядром** и **сервером групповых расписаний**.

## Возможности

- **Расписание:** добавление пар, просмотр сегодня / завтра / недели, ближайшая пара, чётная/нечётная неделя
- **Дедлайны:** задачи по предметам, срок сдачи, сортировка по дате
- **Напоминания:** за 1 час до пары, за 1 день до дедлайна
- **Типы занятий:** лекция, практика, лабораторная + аудитория и преподаватель
- **Импорт/экспорт:** JSON на диске, текстовый экспорт
- **Статистика:** пары в неделю, дедлайны по предметам, загруженность по дням
- **Групповые расписания:** сервер хранит расписания групп, бот синхронизирует их с данными пользователя

## Архитектура

```
studybot/
├── schedule_core/      # чистые функции: расписание, конфликты, валидация
├── sync_server/        # FastAPI, JSON в server_data/groups/
├── bot/                # aiogram, клиент sync_client, команды
├── data/users/         # JSON по user_id
├── server_data/groups/ # расписания групп на сервере
└── tests/
```

## Установка

```bash
cd studybot
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
copy .env.example .env
```

В `.env` укажите `BOT_TOKEN` и при необходимости `SYNC_SERVER_URL` (по умолчанию `http://127.0.0.1:8000`).

## Запуск

**Сервер синхронизации** (в отдельном терминале):

```bash
python -m sync_server
```

Документация API: http://127.0.0.1:8000/docs

**Telegram-бот:**

```bash
python -m bot.main
```

## Команды бота

| Команда | Описание |
|---------|----------|
| `/today`, `/tomorrow`, `/week` | Расписание |
| `/next` | Ближайшая пара |
| `/add_lesson`, `/add_task` | Добавить пару / задачу |
| `/deadlines` | Ближайшие дедлайны |
| `/stats` | Статистика |
| `/export` | Текстовый экспорт |
| `/import` | Импорт JSON |
| `/set_semester YYYY-MM-DD` | Начало семестра (чётность недель) |
| **Группы** (кнопка меню) | Inline-меню: список, создать, синхронизировать, версия, опубликовать |
| `/groups` | То же меню (альтернатива) |

## API сервера

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/health` | Проверка работы |
| GET | `/groups` | Список групп |
| POST | `/groups` | Создать группу |
| GET | `/groups/{group_id}/schedule` | Расписание группы |
| PUT | `/groups/{group_id}/schedule` | Опубликовать/заменить расписание |
| GET | `/groups/{group_id}/version` | Версия, дата обновления, число пар |

Перед сохранением сервер вызывает `schedule_core.validators.validate_schedule()`. При ошибках PUT возвращает HTTP 400 со списком ошибок.

## Пример JSON для публикации расписания группы

Тело запроса `PUT /groups/ИВТ-31/schedule`:

```json
{
  "lessons": [
    {
      "subject": "Математика",
      "weekday": 0,
      "start": "09:00",
      "end": "10:30",
      "room": "301",
      "teacher": "Иванов И.И.",
      "lesson_type": "лекция",
      "week": "both"
    },
    {
      "subject": "Физика",
      "weekday": 2,
      "start": "11:00",
      "end": "12:30",
      "room": "205",
      "teacher": "Петров П.П.",
      "lesson_type": "практика",
      "week": "even"
    }
  ]
}
```

Поле `week`: `"both"`, `"even"` или `"odd"`. Тип занятия: `"лекция"`, `"практика"`, `"лабораторная"`.

## Тесты

```bash
pytest
```

## Разделение работы на двух человек (пополам)

Общий контракт между участниками: формат пары в JSON (см. пример выше) и таблица API. Интеграция: сервер вызывает `validate_schedule()` из ядра; бот ходит на сервер через `sync_client`.

### Участник A — функциональное ядро (~50%)

| Что делает | Файлы |
|------------|--------|
| Модели, сериализация | `schedule_core/models.py`, `io_json.py` |
| Даты, недели, чётность | `schedule_core/dates.py` |
| Расписание на день/неделю, «следующая пара» | `schedule_core/schedule.py` |
| Дедлайны, напоминания, статистика, текст | `deadlines.py`, `reminders.py`, `stats.py`, `format_text.py` |
| Конфликты пар и валидация | `conflicts.py`, `validators.py` |
| Иммутабельные обновления профиля | `user_ops.py` |
| Тесты ядра | `tests/test_dates.py`, `test_schedule.py`, `test_deadlines.py`, `test_stats.py`, `test_conflicts.py`, `test_validators.py`, `test_user_ops.py` |

**Не трогает:** `sync_server/`, `bot/sync_client.py`, `bot/sync_handlers.py`.

**Сдаёт участнику B:** стабильные `Lesson`, `validate_schedule()`, `lessons_to_dict` / `lessons_from_dict`.

### Участник B — сервер и Telegram (~50%)

| Что делает | Файлы |
|------------|--------|
| REST API, хранение групп | `sync_server/app.py`, `storage.py`, `schedule_data.py`, `responses.py`, `__main__.py` |
| HTTP-клиент и команды синхронизации | `bot/sync_client.py`, `bot/sync_handlers.py`, `bot/sync_format.py` |
| Остальной бот (команды, FSM, клавиатуры) | `bot/handlers.py`, `keyboards.py`, `storage.py`, `scheduler.py`, `main.py` |
| Тесты API | `tests/test_sync_server.py` |
| Данные на диске | `data/users/`, `server_data/groups/` |

**Не трогает:** логику конфликтов и валидаторов (только вызывает готовые функции на сервере).

**Сдаёт участнику A:** работающий `SYNC_SERVER_URL`, список endpoints, пример успешного `PUT /groups/.../schedule`.

### Сценарий совместной проверки

1. **B** запускает `python -m sync_server`.
2. **A** убеждается, что `pytest tests/test_conflicts.py tests/test_validators.py` проходит.
3. **B** запускает бота; в Telegram: кнопка **Группы** → **Создать группу** → `ИВТ-31` → добавить пары → **Опубликовать моё расписание**.
4. Второй пользователь: **Группы** → **Список групп** → `ИВТ-31` → **Синхронизировать** → **Сегодня** — то же расписание, свои дедлайны остаются.

### Групповое расписание в боте (зона B)

Кнопка **«Группы»** в нижнем меню → inline-кнопки под сообщением:

| Кнопка | Действие |
|--------|----------|
| Список групп | Выбор группы кнопкой (подписка) |
| Создать группу | Ввод кода группы текстом |
| Синхронизировать | Загрузить расписание выбранной группы |
| Версия на сервере | Версия и число пар |
| Опубликовать моё расписание | Выложить ваши пары в группу |

Совместная проверка: `/create_group` через кнопку «Создать» → «Синхронизировать» у одногруппника.

## Функциональный стиль (требование курса)

Проект строится как **чистое ядро + эффекты на краях**:

| Принцип | Где в проекте |
|---------|----------------|
| Неизменяемые данные | `dataclass(frozen=True)`: `Lesson`, `Task`, `UserData`, `LessonConflict`, `StoredGroupSchedule` |
| Чистые функции | `schedule_core/*`, `validators`, `conflicts`, `user_ops`, `sync_server/schedule_data.py`, `responses.py`, `bot/sync_format.py` |
| Без мутаций списков | Результаты — `tuple`, обновление — `dataclasses.replace` / `user_ops` |
| Композиция | `map`, `filter`, `sorted`, `min`, `groupby`, `combinations`, генераторы |
| Разделение слоёв | I/O только в `io_json`, `storage`, `sync_client`; Telegram — в `handlers` |

**Примеры чистых функций:**

- `lessons_overlap`, `find_lesson_conflicts` — проверка без побочных эффектов
- `validate_schedule` = `lesson_errors_for_schedule` + `conflict_errors_for_schedule`
- `replace_lessons(user, lessons)` — новый `UserData`, старый не меняется
- `format_sync_success(...)` — строка из аргументов, без обращения к БД

**Эффекты (допустимы на границе):** запись JSON, HTTP, Telegram `await` — не в `schedule_core`.
