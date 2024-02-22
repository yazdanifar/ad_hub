from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import models

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@localhost/ad_hub"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
models.Base.metadata.create_all(bind=engine)


def get_db():
    db = session_factory()
    try:
        yield db
    finally:
        db.close()
