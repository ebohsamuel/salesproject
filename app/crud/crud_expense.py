import calendar
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, select
from app import models
from app.schema import schema_expense
import re


YEAR_PATTERN = re.compile(r"^\d{4}$")  # YYYY
YEAR_MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")  # YYYY-MM
FULL_DATE_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$")  # YYYY-MM-DD


async def get_expense_by_id(db: AsyncSession, expense_id: int):
    result = await db.scalars(select(models.Expense).filter(models.Expense.id == expense_id))
    return result.first()


async def get_expenses(db: AsyncSession):
    result = await db.scalars(
        select(models.Expense)
        .limit(1500)
        .order_by(desc(models.Expense.expense_date))
    )
    return result.all()


async def create_expense(db: AsyncSession, expense: schema_expense.ExpenseCreate):
    db_expense = models.Expense(**expense.model_dump(exclude_none=True))
    try:
        db.add(db_expense)
        await db.commit()
        await db.refresh(db_expense)
        return db_expense
    except SQLAlchemyError as e:
        await db.rollback()
        print(f"An error occurred: {e}")
        raise
    except ValueError as e:
        await db.rollback()
        raise


async def update_expense(db: AsyncSession, expense_id: int, expense_details: dict):
    db_expense = await get_expense_by_id(db, expense_id)
    try:
        if expense_details["description"]:
            db_expense.description = expense_details["description"]
        if expense_details["amount"]:
            db_expense.amount = expense_details["amount"]
        await db.commit()
        await db.refresh(db_expense)
        return db_expense
    except SQLAlchemyError as e:
        await db.rollback()
        print(f"An error occurred: {e}")
        raise
    except ValueError as e:
        await db.rollback()
        raise


async def get_expense_by_date(db: AsyncSession, date_str: str):

    result = None

    if YEAR_PATTERN.match(date_str):
        start_date = datetime.strptime(f"{date_str}-01-01", "%Y-%m-%d").date()
        end_date = datetime.strptime(f"{date_str}-12-31", "%Y-%m-%d").date()
        result = await db.scalars(
            select(models.Expense)
            .order_by(desc(models.Expense.expense_date))
            .filter(models.Expense.expense_date.between(start_date, end_date))
        )
    elif YEAR_MONTH_PATTERN.match(date_str):
        # Query orders for the whole month
        year, month = map(int, date_str.split('-'))
        last_day = calendar.monthrange(year, month)[1]
        start_date = datetime.strptime(f"{date_str}-01", "%Y-%m-%d").date()
        end_date = datetime.strptime(f"{date_str}-{last_day}", "%Y-%m-%d").date()
        result = await db.scalars(
            select(models.Expense)
            .order_by(desc(models.Expense.expense_date))
            .filter(models.Expense.expense_date.between(start_date, end_date))
        )
    elif FULL_DATE_PATTERN.match(date_str):
        # Query orders for the exact date
        result = await db.scalars(
            select(models.Expense)
            .order_by(desc(models.Expense.expense_date))
            .filter(models.Expense.expense_date == datetime.strptime(date_str, "%Y-%m-%d").date())
        )
    return result.all()
