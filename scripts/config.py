"""Хранит пути и конфиг БД."""
from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

# sqlite:/// – sync,  sqlite+aiosqlite:/// – async
SQLALCHEMY_DATABASE_URI = os.getenv(
    "DATABASE_URI",
    f"sqlite+aiosqlite:///{BASE_DIR / 'diary.db'}",
)