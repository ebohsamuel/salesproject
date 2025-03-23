from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from app.schema import schema_product
from sqlalchemy import desc, select
from sqlalchemy.orm import selectinload
from app import models


async def get_product_by_product_name(db: AsyncSession, product_name: str):
    result = await db.scalars(
        select(models.Product)
        .options(
            selectinload(models.Product.stock),
            selectinload(models.Product.purchases),
            selectinload(models.Product.orderitems)
        )
        .filter(models.Product.product_name == product_name)
    )
    return result.first()


async def get_product_by_id(db: AsyncSession, product_id: int):
    result = await db.scalars(
        select(models.Product)
        .options(
            selectinload(models.Product.stock),
            selectinload(models.Product.purchases),
            selectinload(models.Product.orderitems)
        )
        .filter(models.Product.id == product_id)
    )
    return result.first()


async def add_new_product(db: AsyncSession, product: schema_product.ProductCreate):
    db_product = models.Product(**product.model_dump())
    try:
        db.add(db_product)
        await db.commit()
        await db.refresh(db_product)
        return db_product
    except SQLAlchemyError as e:
        await db.rollback()
        print(f"An error occurred: {e}")
        raise
    except ValueError as e:
        await db.rollback()
        raise


async def update_product(db: AsyncSession, product_details: dict, product_id: int):
    db_product = await get_product_by_id(db, product_id)
    try:
        if product_details["product_name"]:
            db_product.product_name = product_details["product_name"]
        if product_details["image_data"]:
            db_product.image_data = product_details["image_data"]
        await db.commit()
        await db.refresh(db_product)
        return db_product
    except SQLAlchemyError as e:
        await db.rollback()
        print(f"An error occurred: {e}")
        raise
    except ValueError as e:
        await db.rollback()
        raise


async def get_all_product(db: AsyncSession):
    result = await db.scalars(
        select(models.Product)
        .options(
            selectinload(models.Product.stock),
            selectinload(models.Product.purchases),
            selectinload(models.Product.orderitems)
        )
    )
    return result.all()
