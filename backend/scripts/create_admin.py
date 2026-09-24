"""Create a local administrator without sharing anyone else's credentials."""
from getpass import getpass
from sqlalchemy import select
from backend.app.database.session import SessionLocal
from backend.app.database.tables.user import User
from backend.app.core.security import hash_password


def main():
    username = input("New admin username: ").strip()
    password = getpass("New password (12+ characters): ")
    if not username or len(password) < 12 or len(password.encode()) > 72:
        raise SystemExit("Enter a username and a password of 12+ characters, at most 72 UTF-8 bytes.")
    if password != getpass("Repeat password: "):
        raise SystemExit("Passwords differ.")
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.username == username)):
            raise SystemExit("Username already exists; no changes made.")
        db.add(User(username=username, password_hash=hash_password(password), role="ADMIN", is_active=True))
        db.commit()
    print("Administrator created.")


if __name__ == "__main__":
    main()
