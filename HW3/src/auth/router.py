from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user_basic
from src.auth.models import User
from src.auth.schemas import Token, UserCreate, UserOut
from src.auth.service import create_access_token, hash_password, verify_password
from src.database import get_db
from src.logger import db_logger

router = APIRouter(tags=["auth"])


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация пользователя",
    description="Эндпоинт для создания нового пользователя.",
)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == data.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already taken")

    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    db_logger.info("user created: id=%s username=%s", user.id, user.username)
    return user


@router.post(
    "/login",
    response_model=Token,
    summary="Вход / получение JWT-токена",
    description="Эндпоинт для авторизации.",
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        db_logger.warning("login failed: %s", form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    db_logger.info("login: user_id=%s", user.id)
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


@router.get(
    "/users/me",
    response_model=UserOut,
    summary="Текущий пользователь (Basic Auth)",
    description=(
        "Возвращает профиль пользователя."

    ),
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user_basic)],
) -> User:
    return current_user
