import calendar

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.schema import schema_purchase
from sqlalchemy import desc, select
from datetime import datetime
from app import models
import re


YEAR_PATTERN = re.compile(r"^\d{4}$")  # YYYY
YEAR_MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")  # YYYY-MM
FULL_DATE_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$")  # YYYY-MM-DD


def add_new_purchase(db: AsyncSession, purchase: schema_purchase.PurchaseCreate):
    db_purchase = models.Purchase(**purchase.model_dump())
    db.add(db_purchase)
    return db_purchase


async def get_purchase_by_id(db: AsyncSession, purchase_id: int):
    result = await db.scalars(
        select(models.Purchase)
        .filter(models.Purchase.id == purchase_id)
    )
    return result.first()


async def get_all_purchase(db: AsyncSession):
    result = await db.scalars(
        select(models.Purchase).limit(1500)
        .options(
            selectinload(models.Purchase.product)
        )
        .order_by(desc(models.Purchase.purchase_date))
    )
    return result.all()


async def get_purchase_by_date(db: AsyncSession, date_str: str):

    result = None

    if YEAR_PATTERN.match(date_str):
        start_date = datetime.strptime(f"{date_str}-01-01","%Y-%m-%d").date()
        end_date = datetime.strptime(f"{date_str}-12-31", "%Y-%m-%d").date()
        result = await db.scalars(
            select(models.Purchase)
            .options(
                selectinload(models.Purchase.product)
            )
            .order_by(desc(models.Purchase.purchase_date))
            .filter(models.Purchase.purchase_date.between(start_date, end_date))
        )
    elif YEAR_MONTH_PATTERN.match(date_str):
        # Query orders for the whole month
        year, month = map(int, date_str.split('-'))
        last_day = calendar.monthrange(year, month)[1]
        start_date = datetime.strptime(f"{date_str}-01", "%Y-%m-%d").date()
        end_date = datetime.strptime(f"{date_str}-{last_day}", "%Y-%m-%d").date()
        result = await db.scalars(
            select(models.Purchase)
            .options(
                selectinload(models.Purchase.product)
            )
            .order_by(desc(models.Purchase.purchase_date))
            .filter(models.Purchase.purchase_date.between(start_date, end_date))
        )
    elif FULL_DATE_PATTERN.match(date_str):
        # Query orders for the exact date
        result = await db.scalars(
            select(models.Purchase)
            .options(
                selectinload(models.Purchase.product)
            )
            .order_by(desc(models.Purchase.purchase_date))
            .filter(models.Purchase.purchase_date == datetime.strptime(date_str, "%Y-%m-%d").date())
        )
    return result.all()


async def update_purchase(db: AsyncSession, purchase_details: dict, purchase_id: int):
    db_purchase = await get_purchase_by_id(db, purchase_id)
    if purchase_details["purchase_date"]:
        db_purchase.purchase_date = purchase_details["purchase_date"]
    if purchase_details["Quantity"]:
        db_purchase.Quantity = purchase_details["Quantity"]
    if purchase_details["unit_cost"]:
        db_purchase.unit_cost = purchase_details["unit_cost"]
    if purchase_details["total_cost"]:
        db_purchase.total_cost = purchase_details["total_cost"]
    if purchase_details.get("product_id"):
        db_purchase.product_id = purchase_details["product_id"]
    return db_purchase
