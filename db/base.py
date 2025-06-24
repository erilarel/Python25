"""
@file
@brief Базовый класс для всех ORM-моделей SQLAlchemy.
@details
Модуль определяет абстрактный базовый класс Base для декларативного стиля SQLAlchemy ORM.
"""

from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """
    @brief Абстрактный базовый класс для всех ORM-моделей.
    @details
    Наследуется всеми моделями приложения для поддержки декларативного синтаксиса SQLAlchemy.
    """
    pass
