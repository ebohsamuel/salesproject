from datetime import date
from fastapi import APIRouter, Depends, Form
from sqlalchemy.ext.asyncio import AsyncSession
from app.authentication import get_db, check_manager
from app.schema import schema_expense, schema_user
from app.crud import crud_expense


router = APIRouter()


@router.post("/expense-add")
async def expense_add(
        expense_date: date | None = Form(default=None),
        description: str | None = Form(default=None),
        amount: int | None = Form(default=None),
        user: schema_user.User = Depends(check_manager),
        db: AsyncSession = Depends(get_db)
):
    expense = schema_expense.ExpenseCreate(
        expense_date=expense_date,
        amount=amount,
        description=description
    )
    db_expense = await crud_expense.create_expense(db, expense)
    return {"detail": "successful"}
