from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from app import models
from app.schema import schema_user
import os

scheme = os.getenv("scheme")
admin_email = os.getenv("admin_email")


pwd_context = CryptContext(schemes=[f"{scheme}"], deprecated="auto")


async def create_user(db: AsyncSession, user: schema_user.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    user_details = user.model_dump(exclude_none=True)
    user_details.pop("password")
    db_user = models.User(**user_details, hashed_password=hashed_password)
    try:
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user
    except SQLAlchemyError as e:
        await db.rollback()
        print(f"An error occurred: {e}")
        raise
    except ValueError as e:
        await db.rollback()
        raise


async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.scalars(select(models.User).filter(models.User.email == email))
    return result.first()


async def get_user_by_id(db: AsyncSession, user_id: int):
    result = await db.scalars(select(models.User).filter(models.User.id == user_id))
    return result.first()


async def get_users(db: AsyncSession):
    result = await db.scalars(select(models.User).where(models.User.email != admin_email))
    return result.all()


async def update_user(db: AsyncSession, user_details: dict, user_id: int):
    db_user = await get_user_by_id(db, user_id)
    try:
        if "is_active" in user_details and user_details["is_active"] is not None:
            db_user.is_active = user_details["is_active"]
        if user_details["user_category"]:
            db_user.user_category = user_details["user_category"]
        if user_details["email"]:
            db_user.email = user_details["email"]
        if user_details["phone"]:
            db_user.phone = user_details["phone"]
        if user_details["fullname"]:
            db_user.fullname = user_details["fullname"]
        if user_details["address"]:
            db_user.address = user_details["address"]
        if user_details["next_of_kin"]:
            db_user.next_of_kin = user_details["next_of_kin"]
        if user_details["phone_next_of_kin"]:
            db_user.phone_next_of_kin = user_details["phone_next_of_kin"]
        if user_details["password"]:
            db_user.hashed_password = pwd_context.hash(user_details["password"])
        await db.commit()
        await db.refresh(db_user)
        return db_user
    except SQLAlchemyError as e:
        await db.rollback()
        print(f"An error occurred: {e}")
        raise
    except ValueError as e:
        await db.rollback()
        raise
