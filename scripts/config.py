"""
@file
@brief Хранит пути и параметры подключения к базе данных.
@details
Модуль определяет базовую директорию проекта, подгружает переменные окружения из .env
и формирует строку подключения к базе данных (SQLite через aiosqlite).
"""

from pathlib import Path
from dotenv import load_dotenv

#: @brief Базовая директория проекта (три уровня вверх от текущего файла).
BASE_DIR = Path(__file__).resolve().parent.parent.parent

#: @brief Загрузка переменных окружения из .env-файла в BASE_DIR.
load_dotenv(BASE_DIR / ".env")

#: @brief Строка подключения SQLAlchemy для асинхронной работы с SQLite.
#: @details Используйте "sqlite+aiosqlite" для асинхронного доступа.
SQLALCHEMY_DATABASE_URI = "sqlite+aiosqlite:///./diary.db"
