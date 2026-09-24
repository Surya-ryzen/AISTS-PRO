from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.app.database.session import SessionLocal
from backend.app.schemas.auth import (
    TokenResponse,
    UserCreate,
    UserResponse,
)
from backend.app.services.auth.exceptions import (
    AuthenticationError,
    UserAlreadyExistsError,
)
from backend.app.services.auth.service import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.post(
    "/register",
    summary="Register a new user",
    response_model=UserResponse,
)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    """
    Register a normal USER account.
    """

    auth_service = AuthService(db)

    try:
        return auth_service.create_user(user_data)

    except UserAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.post(
    "/login",
    summary="Login and obtain an access token",
    response_model=TokenResponse,
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Authenticate a user and return a JWT access token.
    """

    auth_service = AuthService(db)

    try:
        user = auth_service.authenticate_user(
            username=form_data.username,
            password=form_data.password,
        )

        token = auth_service.create_token(user)

        return TokenResponse(
            access_token=token,
            token_type="bearer",
        )

    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )
