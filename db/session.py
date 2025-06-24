from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from .base import Base  # Базовый класс для всех ORM-моделей (Declarative Base)
from scripts.config import SQLALCHEMY_DATABASE_URI  # Строка подключения к БД (задаётся в конфиге/ENV)

#: @brief Асинхронный движок SQLAlchemy.
#: @details Используется для подключения к БД через aiosqlite или asyncpg.
engine = create_async_engine(SQLALCHEMY_DATABASE_URI, echo=False, future=True)

#: @brief Фабрика асинхронных сессий для работы с БД.
#: @details Создаёт экземпляры AsyncSession с нужными параметрами.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,  # Сессия не инвалидируется после commit()
    class_=AsyncSession,
)

async def init_db():
    """
    @brief Создаёт все таблицы в базе данных, если их ещё нет.

    @details
    Используется только для разработки или тестирования, если не настроен Alembic.
    Обычно вызывается при первом запуске приложения.

    @return None
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  # создаёт таблицы по описанию моделей
