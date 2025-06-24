from sqlalchemy import String, Text, DateTime, Float, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base

class Note(Base):
    """
    @brief ORM-модель для хранения одной заметки дневника эмоций.

    Описывает структуру таблицы "notes" для хранения заметок с текстом, аудиофайлом, эмоцией, уверенностью, источником и временными метками.

    @details
    Каждая заметка содержит:
    - текстовое описание
    - (опционально) аудиофайл
    - метку эмоции
    - оценку уверенности классификатора
    - источник создания
    - даты создания и обновления

    Используется в приложении для анализа эмоций пользователя.
    """

    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True
    )
    """@brief Уникальный идентификатор заметки (автоинкремент)."""

    created_at: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.now()
    )
    """@brief Дата и время создания (устанавливается сервером по умолчанию)."""

    updated_at: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    """@brief Дата и время последнего обновления (обновляется автоматически)."""

    text: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    """@brief Основной текст заметки (обязательное поле)."""

    audio_path: Mapped[str | None] = mapped_column(
        String(512), nullable=True
    )
    """@brief Путь к аудиофайлу, если заметка записана голосом (опционально)."""

    emotion: Mapped[str] = mapped_column(
        String(32), nullable=False
    )
    """@brief Метка эмоции (например, joy, sad, anger)."""

    score: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    """@brief Оценка уверенности классификатора эмоций (от 0 до 1, опционально)."""

    source: Mapped[str] = mapped_column(
        String(16), default="voice", nullable=False
    )
    """@brief Источник заметки: voice (по умолчанию), edit, import и т.д."""

    def __repr__(self) -> str:
        """
        @brief Строковое представление объекта Note.

        @return Строка для отладки, включающая id и эмоцию.
        """
        return f"<Note id={self.id} emotion={self.emotion}>"
