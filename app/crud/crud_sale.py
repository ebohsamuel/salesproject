import calendar
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import models
from sqlalchemy import desc, select
from app.schema import schema_sale
import re


YEAR_PATTERN = re.compile(r"^\d{4}$")  # YYYY
YEAR_MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")  # YYYY-MM
FULL_DATE_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$")  # YYYY-MM-DD


async def create_new_order(db: AsyncSession, order: dict, user_id: int):
    db_order = models.Order(**order, user_id=user_id)
    try:
        db.add(db_order)
        await db.commit()
        await db.refresh(db_order)
        return db_order
    except SQLAlchemyError as e:
        await db.rollback()
        print(f"An error occurred: {e}")
        raise
    except ValueError as e:
        await db.rollback()
        raise


async def get_order_by_id(db: AsyncSession, order_id: int):
    result = await db.scalars(select(models.Order).filter(models.Order.id == order_id))
    return result.first()


async def get_order_by_date(db: AsyncSession, date_str: str):
    result = None
    if YEAR_PATTERN.match(date_str):
        start_date = datetime.strptime(f"{date_str}-01-01", "%Y-%m-%d").date()
        end_date = datetime.strptime(f"{date_str}-12-31", "%Y-%m-%d").date()
        result = await db.scalars(select(models.Order).filter(models.Order.order_date.between(start_date, end_date)))
    return result.all()


async def get_all_order(db: AsyncSession):
    result = await db.scalars(
        select(models.Order).limit(1500)
        .options(
            selectinload(models.Order.orderitems),
            selectinload(models.Order.user)
        ).order_by(desc(models.Order.order_date))
    )
    return result.all()


async def get_order_item_by_order_date(db: AsyncSession, date_str: str):
    result = None

    if YEAR_PATTERN.match(date_str):
        start_date = datetime.strptime(f"{date_str}-01-01", "%Y-%m-%d").date()
        end_date = datetime.strptime(f"{date_str}-12-31", "%Y-%m-%d").date()
        subquery = (
            select(models.Order.id, models.Order.order_date)
            .filter(models.Order.order_date.between(start_date, end_date))
            .order_by(desc(models.Order.order_date))
            .subquery()
        )
        result = await db.scalars(
            select(models.OrderItem)
            .where(models.OrderItem.order_id.in_(select(subquery.c.id)))
            .options(
                selectinload(models.OrderItem.order).selectinload(models.Order.user),
                selectinload(models.OrderItem.product)
            ).order_by(desc(models.OrderItem.order_id))
        )
    elif YEAR_MONTH_PATTERN.match(date_str):
        # Query orders for the whole month
        year, month = map(int, date_str.split('-'))
        last_day = calendar.monthrange(year, month)[1]

        start_date = datetime.strptime(f"{date_str}-01", "%Y-%m-%d").date()
        end_date = datetime.strptime(f"{date_str}-{last_day}", "%Y-%m-%d").date()
        subquery = (
            select(models.Order.id, models.Order.order_date)
            .filter(models.Order.order_date.between(start_date, end_date))
            .order_by(desc(models.Order.order_date))
            .subquery()
        )
        result = await db.scalars(
            select(models.OrderItem)
            .where(models.OrderItem.order_id.in_(select(subquery.c.id)))
            .options(
                selectinload(models.OrderItem.order).selectinload(models.Order.user),
                selectinload(models.OrderItem.product)
            ).order_by(desc(models.OrderItem.order_id))
        )
    elif FULL_DATE_PATTERN.match(date_str):
        # Query orders for the exact date
        subquery = (
            select(models.Order.id, models.Order.order_date)
            .filter(models.Order.order_date == datetime.strptime(date_str, "%Y-%m-%d").date())
            .order_by(desc(models.Order.order_date))
            .subquery()
        )
        result = await db.scalars(
            select(models.OrderItem)
            .where(models.OrderItem.order_id.in_(select(subquery.c.id)))
            .options(
                selectinload(models.OrderItem.order).selectinload(models.Order.user),
                selectinload(models.OrderItem.product)
            ).order_by(desc(models.OrderItem.order_id))
        )

    return result.all()


async def get_order_item_between_order_date(db: AsyncSession, start_date: str, end_date: str):
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()

    subquery = (
        select(models.Order.id, models.Order.order_date)
        .filter(models.Order.order_date.between(start, end))
        .order_by(desc(models.Order.order_date))
        .subquery()
    )
    result = await db.scalars(
        select(models.OrderItem)
        .where(models.OrderItem.order_id.in_(select(subquery.c.id)))
        .options(
            selectinload(models.OrderItem.order).selectinload(models.Order.user),
            selectinload(models.OrderItem.product)
        ).order_by(desc(models.OrderItem.order_id))
    )
    return result.all()


def create_new_order_item(db: AsyncSession, item: dict, order_id: int, product_id: int):
    db_order_item = models.OrderItem(**item, order_id=order_id, product_id=product_id)
    db.add(db_order_item)
    return db_order_item


async def get_order_item_by_id(db: AsyncSession, order_item_id: int):
    result = await db.scalars(select(models.OrderItem).filter(models.OrderItem.id == order_item_id))
    return result.first()


async def get_all_order_item(db: AsyncSession):
    subquery = (
        select(models.Order.id, models.Order.order_date)
        .order_by(desc(models.Order.order_date))  # Order first
        .subquery()
    )

    result = await db.scalars(
        select(models.OrderItem).limit(500)
        .where(models.OrderItem.order_id.in_(select(subquery.c.id)))
        .options(
            selectinload(models.OrderItem.order).selectinload(models.Order.user),
            selectinload(models.OrderItem.product)
        ).order_by(desc(models.OrderItem.order_id))
    )
    return result.all()

