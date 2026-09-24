from contextlib import contextmanager

from sqlalchemy.orm import Session

from backend.app.database.session import SessionLocal


@contextmanager
def get_db_session():
    """
    Provides a database session with automatic
    commit, rollback, and cleanup.
    """

    session: Session = SessionLocal()

    try:
        yield session
        session.commit()

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()
