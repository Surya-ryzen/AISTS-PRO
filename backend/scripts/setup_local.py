from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy import select
from backend.app.database.base import Base
from backend.app.database import tables
from backend.app.database.connection import engine
from backend.app.database.session import SessionLocal

if engine.dialect.name != 'sqlite':
    raise SystemExit('This helper is for the local SQLite demo only.')
Base.metadata.create_all(engine)
with SessionLocal() as session:
    if session.scalar(select(tables.Camera).limit(1)) is None:
        session.add(tables.Camera(name='Traffic main', source='datasets/videos/raw/traffic_main.mp4', source_type='file', is_active=True, created_at=datetime.now(timezone.utc)))
        session.commit()
print('Local database ready.')

