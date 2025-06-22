from sqlalchemy import String, Text, DateTime, Float, func
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

class Note(Base):
    """
    ORM-модель для хранения одной заметки дневника эмоций.
    Хранит текст, аудио, эмоцию, уверенность, источник и даты создания/изменения.
    """
    __tablename__ = "notes"

    # Уникальный идентификатор заметки (автоинкремент)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Дата и время создания (ставится сервером по умолчанию)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    # Дата и время последнего обновления (автоматически обновляется при изменениях)
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )

    # Основной текст заметки (обязательное поле)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    # Путь к аудиофайлу, если заметка была записана голосом (опционально)
    audio_path: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Метка эмоции (например, joy, sad, anger) — обязательно
    emotion: Mapped[str] = mapped_column(String(32), nullable=False)

    # Оценка уверенности классификатора эмоций (от 0 до 1, опционально)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Источник заметки: voice (по умолчанию), edit, import и т.д.
    source: Mapped[str] = mapped_column(String(16), default="voice", nullable=False)

    def __repr__(self) -> str:
        # Строковое представление для отладки/логов
        return f"<Note id={self.id} emotion={self.emotion}>"
