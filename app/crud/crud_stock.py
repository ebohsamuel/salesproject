from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.schema import schema_stock
from sqlalchemy import select
from app import models


def add_new_stock(db: AsyncSession, stock: schema_stock.StockCreate):
    db_stock = models.Stock(**stock.model_dump(exclude_none=True))
    db.add(db_stock)
    return db_stock


async def get_stock_with_less_than_alert_balance(db: AsyncSession):
    result = await db.scalars(
        select(models.Stock).where(models.Stock.available_stock <= models.Stock.alert_balance)
        .options(
            selectinload(models.Stock.product)
        )
    )
    return result.all()


async def get_stock_by_product_id(db: AsyncSession, product_id: int):
    result = await db.scalars(
        select(models.Stock)
        .filter(models.Stock.product_id == product_id)
    )
    return result.first()


async def update_stock(db: AsyncSession, stock_details: dict, product_id: int):
    db_stock = await get_stock_by_product_id(db, product_id)
    try:
        if stock_details["price"]:
            db_stock.price = stock_details["price"]
        if stock_details["alert_balance"]:
            db_stock.alert_balance = stock_details["alert_balance"]
        await db.commit()
        await db.refresh(db_stock)
        return db_stock
    except SQLAlchemyError as e:
        await db.rollback()
        print(f"An error occurred: {e}")
        raise
    except ValueError as e:
        await db.rollback()
        raise


async def get_all_stocks(db: AsyncSession):
    result = await db.scalars(
        select(models.Stock)
        .options(
            selectinload(models.Stock.product)
        )
    )
    return result.all()
