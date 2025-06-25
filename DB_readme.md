## Что решает слой DB

* **Надёжно сохраняет заметку** (текст, путь к аудио, эмоция, confidence).
* **Предоставляет чистый API** (`NoteRepository`) — без знания UI/ML‑слоёв.
* **Эволюция схемы через Alembic** — миграции без потери данных.
* **Покрыт асинхронными unit‑тестами** (pytest‑asyncio) — можно не бояться изменений.

---

## Дерево каталогов

```
python25/
├─ db/                    # слой ORM
│   ├─ __init__.py        # делает db/ пакетом Python
│   ├─ base.py            # Declarative Base для моделей
│   ├─ models.py          # схема таблицы notes
│   ├─ session.py         # движок + фабрика сессий, init_db()
│   └─ crud.py            # NoteRepository (add/get/list/update/delete/clear)
│
├─ alembic/               # контроль версий схемы
│   ├─ env.py             # связывает Alembic ↔ SQLAlchemy metadata
│   └─ versions/          # автогенерируемые миграции …
│
├─ tests/
│   ├─ test_crud.py          # базовый CRUD‑тест (smoke)
│   └─ test_crud_extra.py    # расширенные и краевые кейсы (10+ тестов)
│
├─ diary.db               # SQLite‑файл (игнорируется Git‑ом)
├─ requirements.txt       # зависимости
├─ pytest.ini             # настройки pytest / asyncio
└─ README_IGOR_PART.md    # этот файл
```

---

## Зачем каждый файл

| Файл                           | Задача                                                                                                               |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------- |
| **db/base.py**                 | Объявляет `Base` (Declarative Base) для моделей, чтобы Alembic видел схему.                                          |
| **db/models.py**               | Содержит ORM‑класс `Note` — схему таблицы (id, created\_at, updated\_at, text, audio\_path, emotion, score, source). |
| **db/session.py**              | Создаёт engine (`sqlite+aiosqlite`) и `AsyncSessionLocal`. Функция `init_db()` — быстрое создание схемы для dev.     |
| **db/crud.py**                 | Класс `NoteRepository`: все CRUD‑методы + сериализация для фронта.                                                   |
| **alembic/env.py**             | Старт‑скрипт Alembic; подключает `Base.metadata` и строку подключения.                                               |
| **alembic/versions/**          | История миграций (Python‑файлы). Каждая ревизия описывает изменение схемы.                                           |
| **tests/test\_crud.py**        | Минимальный smoke‑тест: добавление, чтение, удаление.                                                                |
| **tests/test\_crud\_extra.py** | Расширенные и edge‑тесты: очистка, сортировка, partial update, пустая таблица и т.д.                                 |
| **requirements.txt**           | Список зависимостей (SQLAlchemy, Alembic, pytest‑asyncio и др.).                                                     |
| **pytest.ini**                 | Включает режим `asyncio_mode = auto` + корректирует PYTHONPATH.                                                      |

---

## Почему разделено на модули

* **Single Responsibility Principle:** каждый слой меняется независимо (можно сменить движок, не трогая crud).
* **Тестируемость:** тесты могут использовать только нужную часть (например, чисто модель + crud).
* **Расширяемость:** легко добавить Users, Tags или перейти на Postgres.
* **Миграции:** структура совместима с Alembic (сразу видит все метаданные).

---

## Быстрый старт

### 1. Установка и окружение (Windows PowerShell)

```powershell
cd A:\python_projects\Python25
python -m venv venv
./venv/Scripts/Activate.ps1
pip install -r requirements.txt
```

*Если видите ошибку ExecutionPolicy:*

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### 2. Миграции (prod / CI)

```powershell
alembic upgrade head
```

### 3. Обновление Alembic

```powershell
alembic upgrade head
```

### 4. Запуск unit‑тестов

```powershell
pytest -q
# Вывод: .......... (10 passed in X.XXs)
```

---

## Функционал слоя ORM + DB

### Модель `Note`

* текст, эмоция, путь к аудио, уверенность ML (score), источник (voice/edit/import)
* автоматические временные метки (`created_at`, `updated_at`)
* поддержка любых типов заметок (ручной ввод, голос, импорт)

### Класс-репозиторий `NoteRepository`

Методы:

* `add()` — добавить заметку (обязательны text, emotion)
* `get()` — получить запись по id
* `list()` — получить последние записи (limit, offset, сортировка по времени)
* `update()` — изменить поля по id (partial update)
* `delete()` — удалить запись
* `clear()` — очистить таблицу (dev/test)
* Все методы поддерживают параметр `as_dict=True` для сериализации в dict (JSON‑friendly)

Асинхронность: все методы async, подходят для FastAPI, Streamlit, ML‑пайплайнов.

---

## Alembic‑миграции

* любые изменения схемы (новые поля, новые таблицы) делаются через Alembic (`alembic revision --autogenerate`)
* миграции применяются через `alembic upgrade head` — данные не теряются

---

## Описание тестов

Все тесты асинхронные, используют in‑memory SQLite (не портят реальную БД).

| Тест                                       | Сценарий                                  |
| ------------------------------------------ | ----------------------------------------- |
| test\_list\_and\_pagination                | Добавление 3 записей, проверка сортировки |
| test\_update\_note                         | Изменение всех полей и времени обновления |
| test\_delete\_note                         | Удаление и повторный поиск                |
| test\_get\_nonexistent                     | Получение несуществующей записи           |
| test\_update\_nonexistent                  | Update для несуществующего id (None)      |
| test\_add\_with\_all\_fields               | Создание со всеми полями                  |
| test\_update\_partial\_fields              | Изменение только одного поля              |
| test\_delete\_nonexistent\_is\_silent      | Удаление несуществующего id (без ошибки)  |
| test\_list\_empty\_then\_filled            | Работа с пустой таблицей, проверка id     |
| test\_get\_returns\_none\_for\_missing\_id | Ещё одна проверка на пустой результат     |

---
**Пример использования репозитория:**

   ```python
import asyncio
from db.session import AsyncSessionLocal, init_db
from db.crud import NoteRepository

async def main():
    # 1) Создаём схему, если её ещё нет
    await init_db()

    async with AsyncSessionLocal() as session:
        repo = NoteRepository(session)

        # 2) Очищаем таблицу
        await repo.clear()

        # 3) Создаём две заметки
        note1 = await repo.add(
            text="Сегодня отличное настроение!",
            emotion="joy",
            score=0.98,
            source="voice",
            audio_path="2024-06-22_12-22-10.ogg",
            as_dict=True,
        )
        note2 = await repo.add(
            text="Я устал",
            emotion="sad",
            score=0.50,
            source="voice",
            audio_path="2024-06-22_12-22-10.ogg",
            as_dict=True,
        )
        print("Добавлены:", note1, note2)

        # 4) Получаем вторую по её реальному ID
        fetched = await repo.get(note2["id"], as_dict=True)
        print("Из базы:", fetched)

        # 5) Обновляем эмоцию и confidence
        updated = await repo.update(
            note2["id"],
            emotion="surprised",
            score=0.80,
            as_dict=True
        )
        print("После апдейта:", updated)

        # 6) Список всех заметок (последние сверху)
        notes = await repo.list(limit=10, offset=0, as_dict=True)
        print("Все заметки:", notes)

        # 7) Удаляем первую
        await repo.delete(note1["id"])
        print(f"Заметка id={note1['id']} удалена!")

if __name__ == "__main__":
    asyncio.run(main())

   ```

