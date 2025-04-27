from datetime import timedelta, datetime, timezone
from typing import Annotated

import jwt
from fastapi import Cookie, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from jwt import InvalidTokenError, ExpiredSignatureError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from app.crud import crud_user
from app.database import async_SessionLocal
from app.schema import schema_token, schema_user
import os

template = Jinja2Templates(directory="app/templates")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")


async def get_db():
    async with async_SessionLocal() as session:
        yield session


class NotAuthenticatedException(HTTPException):
    def __init__(self):
        super().__init__(status_code=401, detail="Not authenticated")


async def authenticate_user(db: AsyncSession, email: str, password: str):
    user_data = await crud_user.get_user_by_email(db, email)
    if not user_data:
        return False
    if not crud_user.pwd_context.verify(password, user_data.hashed_password):
        return False
    return user_data


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(access_token: str | None = Cookie(default=None), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if access_token is None:
        raise NotAuthenticatedException()

    token = access_token[len("Bearer "):]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schema_token.TokenData(username=email)
    except ExpiredSignatureError:
        raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    user_data = await crud_user.get_user_by_email(db, email=token_data.username)
    if user_data is None:
        raise credentials_exception
    return user_data


async def get_current_active_user(current_user: Annotated[schema_user.User, Depends(get_current_user)]):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def check_manager(user: schema_user.User = Depends(get_current_active_user)):
    if user.user_category != 'manager':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have the necessary permissions.")
    return user


async def check_staff(user: schema_user.User = Depends(get_current_active_user)):
    if user.user_category != 'staff':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have the necessary permissions.")
    return user
