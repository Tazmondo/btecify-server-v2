from os import getcwd, environ
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

dbname = "app.db"
if environ.get('testdb'):
    dbname = "test.db"

if Path(getcwd()).name == 'btecify-server':
    SQLALCHEMY_DATABASE_URL = "sqlite:///./db/" + dbname
elif Path(getcwd()).name == "app":
    SQLALCHEMY_DATABASE_URL = "sqlite:///../db/" + dbname
else:
    raise Exception(f"Unknown path: {getcwd()}")

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()
