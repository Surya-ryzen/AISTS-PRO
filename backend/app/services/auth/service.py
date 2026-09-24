from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from backend.app.database.tables.user import User
from backend.app.schemas.auth import UserCreate

from backend.app.services.auth.exceptions import (
    AuthenticationError,
    UserAlreadyExistsError,
)


class AuthService:
    """
    Handles authentication and user management.
    """

    def __init__(self, db: Session):
        self.db = db

    def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user with a hashed password.
        """

        existing_user = self.db.scalar(
            select(User).where(User.username == user_data.username)
        )

        if existing_user:
            raise UserAlreadyExistsError("Username already exists")

        user = User(
            username=user_data.username,
            password_hash=hash_password(user_data.password),
            role="USER",
            is_active=True,
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user

    def authenticate_user(
        self,
        username: str,
        password: str,
    ) -> User:
        """
        Verify username and password.
        """

        user = self.db.scalar(select(User).where(User.username == username))

        if not user:
            raise AuthenticationError("Invalid username or password")

        if not user.is_active:
            raise AuthenticationError("User account is inactive")

        if not verify_password(
            password,
            user.password_hash,
        ):
            raise AuthenticationError("Invalid username or password")

        return user

    def create_token(self, user: User) -> str:
        """
        Create an access token for an authenticated user.
        """

        return create_access_token(
            {
                "sub": str(user.id),
                "username": user.username,
                "role": user.role,
            }
        )
