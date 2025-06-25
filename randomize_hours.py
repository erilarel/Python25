import random
from datetime import datetime, timedelta
from db.session import AsyncSessionLocal
from db.crud import NoteRepository
import asyncio


async def randomize_hours():
    async with AsyncSessionLocal() as session:
        repo = NoteRepository(session)
        notes = await repo.list(limit=None, as_dict=True)

        for note in notes:
            # Сохраняем оригинальную дату
            original_date = datetime.fromisoformat(note['created_at'])
            # Меняем только час
            new_hour = random.randint(0, 23)
            new_date = original_date.replace(hour=new_hour)
            # Обновляем запись
            await repo.update(note['id'], created_at=new_date)

        await session.commit()
        print(f"Обновлено {len(notes)} записей")


if __name__ == "__main__":
    asyncio.run(randomize_hours())