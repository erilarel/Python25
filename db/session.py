from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from .base import Base                     # Базовый класс для всех ORM-моделей (Declarative Base)
from scripts.config import SQLALCHEMY_DATABASE_URI  # Строка подключения к БД (SQLite или Postgres, задаётся в конфиге/ENV)

# Создаём асинхронный движок SQLAlchemy (через aiosqlite)
engine = create_async_engine(SQLALCHEMY_DATABASE_URI, echo=False, future=True)

# Фабрика асинхронных сессий для работы с БД
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,   # сессия не инвалидируется после commit(), удобно для re‑read
    class_=AsyncSession,
)

async def init_db():
    """
    Создать таблицы, если их ещё нет.
    Вызывать только для разработки, если нет Alembic (напр., первый запуск, тесты).
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)   # создаёт таблицы по описанию моделей
