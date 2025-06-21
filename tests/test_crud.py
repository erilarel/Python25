import pytest
import asyncio
from datetime import datetime

from db.session import engine, AsyncSessionLocal
from db import models
from db.crud import NoteRepository


# ───────────────────────── фикстуры ─────────────────────────
@pytest.fixture(autouse=True, scope="module")
async def prepare_db():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.drop_all)


@pytest.fixture
async def repo():
    async with AsyncSessionLocal() as session:
        yield NoteRepository(session)


def _check_basic(note, *, text, emotion, score, source):
    assert note["text"] == text
    assert note["emotion"] == emotion
    assert note["score"] == score
    assert note["source"] == source


# ───────────────────────── обычные кейсы ─────────────────────
@pytest.mark.asyncio
async def test_list_and_pagination(repo):
    await repo.clear()
    for n in range(3):
        await repo.add(text=f"note {n}", emotion="neutral", source="edit")
        await asyncio.sleep(1)        # обеспечиваем разницу секунд
    notes = await repo.list(as_dict=True)
    assert [n["text"] for n in notes] == ["note 2", "note 1", "note 0"]

    page2 = await repo.list(limit=1, offset=1, as_dict=True)
    assert page2[0]["text"] == "note 1"


@pytest.mark.asyncio
async def test_update_note(repo):
    await repo.clear()
    note = await repo.add(text="orig", emotion="sad", as_dict=True)
    await asyncio.sleep(1)
    updated = await repo.update(
        note["id"], text="updated", emotion="joy", score=0.99, as_dict=True
    )
    _check_basic(updated, text="updated", emotion="joy",
                 score=0.99, source="voice")
    assert updated["updated_at"] > note["updated_at"]


@pytest.mark.asyncio
async def test_delete_note(repo):
    await repo.clear()
    note = await repo.add(text="to delete", emotion="sad", as_dict=True)
    await repo.delete(note["id"])
    assert await repo.get(note["id"], as_dict=True) is None


@pytest.mark.asyncio
async def test_get_nonexistent(repo):
    assert await repo.get(9999, as_dict=True) is None


@pytest.mark.asyncio
async def test_update_nonexistent(repo):
    assert await repo.update(12345, text="ghost", as_dict=True) is None


# ───────────────────────── краевые ───────────────────────────
@pytest.mark.asyncio
async def test_add_with_all_fields(repo):
    await repo.clear()
    note = await repo.add(
        text="edge–case",
        emotion="sad",
        score=0.01,
        source="import",
        audio_path="/tmp/edge.wav",
        as_dict=True,
    )
    _check_basic(note, text="edge–case", emotion="sad",
                 score=0.01, source="import")
    assert note["audio_path"].endswith("edge.wav")
    datetime.fromisoformat(note["created_at"])


@pytest.mark.asyncio
async def test_update_partial_fields(repo):
    await repo.clear()
    note = await repo.add(text="orig-text", emotion="joy", as_dict=True)
    await asyncio.sleep(1)
    updated = await repo.update(note["id"], text="only-text-changed",
                                as_dict=True)
    _check_basic(updated, text="only-text-changed",
                 emotion="joy", score=None, source="voice")


@pytest.mark.asyncio
async def test_delete_nonexistent_is_silent(repo):
    await repo.clear()
    await repo.delete(123456)
    note = await repo.add(text="still works", emotion="neutral", as_dict=True)
    assert note["id"]


@pytest.mark.asyncio
async def test_list_empty_then_filled(repo):
    await repo.clear()
    assert await repo.list(as_dict=True) == []

    a = await repo.add(text="a", emotion="joy", as_dict=True)
    await asyncio.sleep(1)
    b = await repo.add(text="b", emotion="sad", as_dict=True)

    ids = [n["id"] for n in await repo.list(as_dict=True)]
    assert ids == [b["id"], a["id"]]


@pytest.mark.asyncio
async def test_get_returns_none_for_missing_id(repo):
    assert await repo.get(987654321, as_dict=True) is None
