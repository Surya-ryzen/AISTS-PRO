from sqlalchemy.orm import sessionmaker

from backend.app.database.connection import engine

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine,
)
