from __future__ import annotations

"""Асинхронный репозиторий + сериализация для фронта (UI / REST).

Функциональность
----------------
* CRUD-методы (add • get • list • update • delete).
* `as_dict=True` ⇒ возвращает NoteDTO (dict), иначе ORM-объект Note.
* list() выдаёт последние заметки: ORDER BY updated_at DESC, created_at DESC.
* clear() быстро очищает всю таблицу (dev-режим, тесты).
"""

from typing import Sequence, Any, TypedDict, overload
from datetime import datetime, timezone

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Note


# ─────────────────── DTO тип ───────────────────
class NoteDTO(TypedDict):
    id: int
    created_at: str
    updated_at: str
    text: str
    audio_path: str | None
    emotion: str
    score: float | None
    source: str


# ──────────────── Репозиторий ───────────────────
class NoteRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # ---------- helpers ----------
    @staticmethod
    def _to_dto(note: Note) -> NoteDTO:
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

    # ---------- add ----------
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
                  as_dict: bool = False):  # type: ignore[override]
        note = Note(text=text, emotion=emotion, score=score,
                    source=source, audio_path=audio_path)
        self.session.add(note)
        await self.session.commit()
        await self.session.refresh(note)
        return self._to_dto(note) if as_dict else note

    # ---------- get ----------
    @overload
    async def get(self, note_id: int, *, as_dict: bool = False) -> Note | None: ...

    @overload
    async def get(self, note_id: int, *, as_dict: bool = True) -> NoteDTO | None: ...

    async def get(self, note_id: int, *, as_dict: bool = False):  # type: ignore[override]
        note = await self.session.get(Note, note_id)
        if note is None:
            return None
        return self._to_dto(note) if as_dict else note

    # ---------- list ----------
    @overload
    async def list(self, *, limit: int = 20, offset: int = 0,
                   as_dict: bool = False) -> Sequence[Note]: ...

    @overload
    async def list(self, *, limit: int = 20, offset: int = 0,
                   as_dict: bool = True) -> list[NoteDTO]: ...

    async def list(self, *, limit: int = 20, offset: int = 0,
                   as_dict: bool = False):  # type: ignore[override]
        res = await self.session.execute(
            select(Note)
            .order_by(Note.updated_at.desc(), Note.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        notes = res.scalars().all()
        return [self._to_dto(n) for n in notes] if as_dict else notes

    # ---------- update ----------
    @overload
    async def update(self, note_id: int, *, as_dict: bool = False,
                     **fields: Any) -> Note | None: ...

    @overload
    async def update(self, note_id: int, *, as_dict: bool = True,
                     **fields: Any) -> NoteDTO | None: ...

    async def update(self, note_id: int, *, as_dict: bool = False,
                     **fields: Any):  # type: ignore[override]
        note: Note | None = await self.session.get(Note, note_id)
        if note is None:
            return None

        # меняем переданные поля
        for key, val in fields.items():
            setattr(note, key, val)

        # руками обновляем timestamp
        note.updated_at = datetime.now(tz=timezone.utc)

        await self.session.commit()
        await self.session.refresh(note)
        return self._to_dto(note) if as_dict else note

    # ---------- delete ----------
    async def delete(self, note_id: int) -> None:
        await self.session.execute(delete(Note).where(Note.id == note_id))
        await self.session.commit()

    # ---------- clear ----------
    async def clear(self) -> None:
        """Стереть все записи (dev / тесты)."""
        await self.session.execute(delete(Note))
        await self.session.commit()
