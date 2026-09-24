"""Isolated SQLite demonstration on port 8001; does not alter the Week 9 database."""
import os
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
os.chdir(ROOT)
private = ROOT / '.week10-local'
private.mkdir(exist_ok=True)
secret = private / 'secret.txt'
password_file = private / 'admin-password.txt'
for file in (secret, password_file):
    if not file.exists():
        file.write_text(secrets.token_urlsafe(24), encoding='utf-8')
defaults = dict(APP_NAME='AI Traffic Week10', APP_ENV='development', DEBUG='false',
    SECRET_KEY=secret.read_text().strip(), API_HOST='127.0.0.1', API_PORT='8001',
    DATABASE_URL='sqlite:///' + (private / 'week10.db').as_posix(), LOG_LEVEL='INFO',
    MODEL_PATH='yolov8s.pt', ALLOWED_ORIGINS='http://127.0.0.1:8001',
    PROJECT_NAME='AI Traffic Week10', VERSION='0.1.0')
for key, value in defaults.items():
    os.environ[key] = value

if __name__ == '__main__':
    from sqlalchemy import select
    from backend.app.database.base import Base
    from backend.app.database import tables
    from backend.app.database.connection import engine
    from backend.app.database.session import SessionLocal
    from backend.app.core.security import hash_password
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if not db.scalar(select(tables.User).where(tables.User.username == 'week10admin')):
            db.add(tables.User(username='week10admin', password_hash=hash_password(password_file.read_text().strip()), role='ADMIN'))
            db.commit()
    print('Open http://127.0.0.1:8001/docs')
    print('Username: week10admin. Password is stored locally in: ' + str(password_file))
    import uvicorn
    uvicorn.run('backend.app.week10_main:app', host='127.0.0.1', port=8001)
