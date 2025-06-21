"""Хранит пути и конфиг БД."""
from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

# sqlite:/// – sync,  sqlite+aiosqlite:/// – async
SQLALCHEMY_DATABASE_URI = "sqlite+aiosqlite:///./diary.db"
