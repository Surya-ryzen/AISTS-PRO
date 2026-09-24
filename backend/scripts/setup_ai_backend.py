"""Add new AI/backend tables without altering or deleting existing project data."""
from backend.app.database.connection import engine
from backend.app.database import tables
from backend.app.database.base import Base

if __name__=='__main__':
    Base.metadata.create_all(engine)
    print('AI/backend tables ready.')
