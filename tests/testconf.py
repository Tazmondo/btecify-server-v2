from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app, getdb
from app.models import Base

DBNAME = "../db/test.db"

with open(DBNAME, "w") as f:
    pass  # Overwrite db with no data

SQLALCHEMY_DATABASE_URL = "sqlite:///" + DBNAME

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def get_test_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[getdb] = get_test_db

client = TestClient(app)
