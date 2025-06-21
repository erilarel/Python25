# tests/test_crud_extra.py
import pytest
from datetime import datetime
from sqlalchemy import delete

from db.session import engine, AsyncSessionLocal
from db import models
from db.crud import NoteRepository


# ─────────────────────────── фикстуры ────────────────────────────
@pytest.fixture(autouse=True, scope="module")
async def prepare_db():
    """Создаём схему до запусков и удаляем после модуля."""
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.drop_all)


@pytest.fixture
async def repo():
    """Свежий NoteRepository на каждую функцию-тест."""
    async with AsyncSessionLocal() as session:
        yield NoteRepository(session)


# ─────────────────────── помощник-ассерт ────────────────────────
def _check_basic(note, *, text, emotion, score, source):
    assert note.text == text
    assert note.emotion == emotion
    assert note.score == score
    assert note.source == source


# ─────────────────────────── обычные кейсы ───────────────────────
@pytest.mark.asyncio
async def test_list_and_pagination(repo):
    for n in range(3):
        await repo.add(text=f"note {n}", emotion="neutral", source="edit")
    notes = await repo.list()
    assert len(notes) == 3

    page2 = await repo.list(limit=1, offset=1)
    assert len(page2) == 1 and page2[0].text == "note 1"


@pytest.mark.asyncio
async def test_update_note(repo):
    note = await repo.add(text="orig", emotion="sad")
    updated = await repo.update(
        note.id, text="updated", emotion="joy", score=0.99
    )
    assert updated.text == "updated"
    assert updated.emotion == "joy"
    assert updated.score == 0.99
    assert updated.updated_at is not None


@pytest.mark.asyncio
async def test_delete_note(repo):
    note = await repo.add(text="to delete", emotion="sad")
    await repo.delete(note.id)
    assert await repo.get(note.id) is None


@pytest.mark.asyncio
async def test_get_nonexistent(repo):
    assert await repo.get(9999) is None


@pytest.mark.asyncio
async def test_update_nonexistent(repo):
    assert await repo.update(12345, text="ghost") is None


# ─────────────────────────── краевые кейсы ───────────────────────
@pytest.mark.asyncio
async def test_add_with_all_fields(repo):
    note = await repo.add(
        text="edge–case",
        emotion="sad",
        score=0.01,
        source="import",
        audio_path="/tmp/edge.wav",
    )
    _check_basic(note, text="edge–case", emotion="sad",
                 score=0.01, source="import")
    assert note.audio_path.endswith("edge.wav")
    assert isinstance(note.created_at, datetime)
    assert note.updated_at is not None           # теперь NOT NULL от сервера


@pytest.mark.asyncio
async def test_update_partial_fields(repo):
    note = await repo.add(text="orig-text", emotion="joy")
    updated = await repo.update(note.id, text="only-text-changed")
    _check_basic(updated, text="only-text-changed",
                 emotion="joy", score=None, source="voice")
    assert updated.updated_at is not None


@pytest.mark.asyncio
async def test_delete_nonexistent_is_silent(repo):
    await repo.delete(123456)                     # чужого id нет — тишина
    note = await repo.add(text="still works", emotion="neutral")
    assert note.id                                # CRUD жив


@pytest.mark.asyncio
async def test_list_empty_then_filled(repo):
    # очищаем таблицу
    async with repo.session.begin():
        await repo.session.execute(delete(models.Note))
        await repo.session.commit()

    assert await repo.list() == []                # пусто

    a = await repo.add(text="a", emotion="joy")
    b = await repo.add(text="b", emotion="sad")
    ids = [n.id for n in await repo.list()]
    assert ids == [a.id, b.id]                    # id ASC


@pytest.mark.asyncio
async def test_get_returns_none_for_missing_id(repo):
    assert await repo.get(987654321) is None
