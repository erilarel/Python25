from typing import Sequence, Any
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Note

class NoteRepository:
    """
    Асинхронный репозиторий для работы с таблицей 'notes'.
    Предоставляет чистый интерфейс для CRUD-операций (create, read, update, delete).
    Использует асинхронную сессию SQLAlchemy.
    """

    def __init__(self, session: AsyncSession):
        """
        Инициализация репозитория с заданной асинхронной сессией.
        Один экземпляр — одна сессия (рекомендуется: session-per-request).
        """
        self.session = session

    async def add(
            self,
            *,
            text: str,
            emotion: str,
            score: float | None = None,
            source: str = "voice",
            audio_path: str | None = None,
    ) -> Note:
        """
        Добавить новую заметку в БД.
        :param text: основной текст заметки (обязателен)
        :param emotion: распознанная эмоция (обязателен)
        :param score: уровень уверенности ML (0..1, опционально)
        :param source: источник заметки (voice, edit, import и т.д.)
        :param audio_path: путь к аудиофайлу (если был)
        :return: созданный объект Note с заполненным id и датами
        """
        note = Note(
            text=text,
            emotion=emotion,
            score=score,
            source=source,
            audio_path=audio_path
        )
        self.session.add(note)
        await self.session.commit()
        await self.session.refresh(note)  # обновляем поля из БД (id, created_at...)
        return note

    async def get(self, note_id: int) -> Note | None:
        """
        Получить заметку по id.
        :param note_id: идентификатор записи
        :return: объект Note или None, если не найден
        """
        res = await self.session.execute(
            select(Note).where(Note.id == note_id)
        )
        return res.scalar_one_or_none()

    async def list(self, limit: int = 20, offset: int = 0) -> Sequence[Note]:
        """
        Получить список заметок (с пагинацией, отсортировано по id).
        :param limit: максимальное число записей (по умолчанию 20)
        :param offset: смещение для пагинации (по умолчанию 0)
        :return: список Note (Sequence[Note])
        """
        res = await self.session.execute(
            select(Note)
            .order_by(Note.id.asc())
            .offset(offset)
            .limit(limit)
        )
        return res.scalars().all()

    async def update(self, note_id: int, **fields: Any) -> Note | None:
        """
        Обновить указанные поля заметки по id.
        :param note_id: идентификатор записи
        :param fields: любые поля модели Note (text, emotion, score, ...)
        :return: обновлённый объект Note, либо None если не найден
        """
        await self.session.execute(
            update(Note).where(Note.id == note_id).values(**fields)
        )
        await self.session.commit()
        return await self.get(note_id)

    async def delete(self, note_id: int) -> None:
        """
        Удалить заметку по id (ничего не делает, если запись не найдена).
        :param note_id: идентификатор записи
        """
        await self.session.execute(
            delete(Note).where(Note.id == note_id)
        )
        await self.session.commit()
