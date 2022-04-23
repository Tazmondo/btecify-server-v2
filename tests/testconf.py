from os import environ

environ['testdb'] = "1"

from app.db import SessionLocal


def get_test_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
