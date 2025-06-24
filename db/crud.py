from __future__ import annotations

from typing import Sequence, Any, TypedDict, overload
from datetime import datetime, timezone

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Note


class NoteDTO(TypedDict):
    """
    @brief Data Transfer Object для заметки Note.

    Используется для сериализации заметки (например, при передаче данных на фронт).
    """
    id: int
    created_at: str
    updated_at: str
    text: str
    audio_path: str | None
    emotion: str
    score: float | None
    source: str


class NoteRepository:
    """
    @brief Асинхронный репозиторий для работы с заметками.

    Позволяет выполнять основные CRUD-операции, а также сериализацию заметок для UI/REST.
    """

    def __init__(self, session: AsyncSession):
        """
        @brief Конструктор репозитория заметок.
        @param session Асинхронная сессия SQLAlchemy.
        """
        self.session = session

    @staticmethod
    def _to_dto(note: Note) -> NoteDTO:
        """
        @brief Преобразует ORM-объект Note в NoteDTO.

        @param note ORM-объект Note.
        @return Словарь с данными заметки (NoteDTO).
        """
        iso = lambda dt: dt.isoformat(sep="T", timespec="seconds") if isinstance(dt, datetime) else None  # noqa: E731
        return NoteDTO(
            id=note.id,
            created_at=iso(note.created_at),
            updated_at=iso(note.updated_at),
            text=note.text,
            audio_path=note.audio_path,
            emotion=note.emotion,
            score=note.score,
            source=note.source,
        )

    @overload
    async def add(self, *, text: str, emotion: str, score: float | None = None,
                  source: str = "voice", audio_path: str | None = None,
                  as_dict: bool = False) -> Note: ...
    @overload
    async def add(self, *, text: str, emotion: str, score: float | None = None,
                  source: str = "voice", audio_path: str | None = None,
                  as_dict: bool = True) -> NoteDTO: ...

    async def add(self, *, text: str, emotion: str, score: float | None = None,
                  source: str = "voice", audio_path: str | None = None,
                  as_dict: bool = False):
        """
        @brief Добавляет новую заметку в базу данных.

        @param text Текст заметки.
        @param emotion Эмоция, определённая для заметки.
        @param score Оценка уверенности (опционально).
        @param source Источник заметки (по умолчанию "voice").
        @param audio_path Путь к аудиофайлу (опционально).
        @param as_dict Если True — возвращает NoteDTO, иначе объект Note.
        @return Добавленная заметка (Note или NoteDTO).
        """
        note = Note(text=text, emotion=emotion, score=score,
                    source=source, audio_path=audio_path)
        self.session.add(note)
        await self.session.commit()
        await self.session.refresh(note)
        return self._to_dto(note) if as_dict else note

    @overload
    async def get(self, note_id: int, *, as_dict: bool = False) -> Note | None: ...
    @overload
    async def get(self, note_id: int, *, as_dict: bool = True) -> NoteDTO | None: ...

    async def get(self, note_id: int, *, as_dict: bool = False):
        """
        @brief Получает заметку по ID.

        @param note_id ID заметки.
        @param as_dict Если True — возвращает NoteDTO, иначе объект Note.
        @return Заметка (Note или NoteDTO), либо None если не найдено.
        """
        note = await self.session.get(Note, note_id)
        if note is None:
            return None
        return self._to_dto(note) if as_dict else note

    @overload
    async def list(self, *, limit: int = 20, offset: int = 0,
                   as_dict: bool = False) -> Sequence[Note]: ...
    @overload
    async def list(self, *, limit: int = 20, offset: int = 0,
                   as_dict: bool = True) -> list[NoteDTO]: ...

    async def list(self, *, limit: int = 20, offset: int = 0,
                   as_dict: bool = False):
        """
        @brief Получает список заметок, отсортированных по времени обновления/создания.

        @param limit Максимальное количество заметок.
        @param offset Смещение (для постраничности).
        @param as_dict Если True — возвращает список NoteDTO, иначе список Note.
        @return Список заметок (Note или NoteDTO).
        """
        res = await self.session.execute(
            select(Note)
            .order_by(Note.updated_at.desc(), Note.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        notes = res.scalars().all()
        return [self._to_dto(n) for n in notes] if as_dict else notes

    @overload
    async def update(self, note_id: int, *, as_dict: bool = False,
                     **fields: Any) -> Note | None: ...
    @overload
    async def update(self, note_id: int, *, as_dict: bool = True,
                     **fields: Any) -> NoteDTO | None: ...

    async def update(self, note_id: int, *, as_dict: bool = False,
                     **fields: Any):
        """
        @brief Обновляет существующую заметку по ID.

        @param note_id ID заметки.
        @param as_dict Если True — возвращает NoteDTO, иначе Note.
        @param fields Поля для обновления (ключ-значение).
        @return Обновлённая заметка (Note или NoteDTO), либо None если не найдено.
        """
        note: Note | None = await self.session.get(Note, note_id)
        if note is None:
            return None

        # Меняем переданные поля
        for key, val in fields.items():
            setattr(note, key, val)

        # Обновляем timestamp вручную
        note.updated_at = datetime.now(tz=timezone.utc)

        await self.session.commit()
        await self.session.refresh(note)
        return self._to_dto(note) if as_dict else note

    async def delete(self, note_id: int) -> None:
        """
        @brief Удаляет заметку по ID.

        @param note_id ID заметки.
        """
        await self.session.execute(delete(Note).where(Note.id == note_id))
        await self.session.commit()

    async def clear(self) -> None:
        """
        @brief Удаляет все заметки из таблицы (для тестов и dev-режима).
        """
        await self.session.execute(delete(Note))
        await self.session.commit()
