from datetime import datetime, UTC
from fastapi import APIRouter, Depends, Form, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.authentication import get_db, template, check_manager, get_current_active_user
from app.crud import crud_expense
from app.schema import schema_user


router = APIRouter(dependencies=[Depends(get_current_active_user)])


@router.get("/expenses")
async def expense_(
        request: Request,
        db: AsyncSession = Depends(get_db),
        user: schema_user.User = Depends(get_current_active_user)
):
    expenses = await crud_expense.get_expenses(db)
    return template.TemplateResponse(
        "expenses.html",
        {"request": request, "expenses": expenses, "full_name": user.fullname}
    )


@router.get("/expense-data")
async def expense_list(date_str: str, db: AsyncSession = Depends(get_db)):
    expenses = await crud_expense.get_expense_by_date(db, date_str)
    return {"data": expenses}


@router.post("/expense/update")
async def expense_update_submit(
        expense_id: int = Form(),
        description: str | None = Form(default=None),
        amount: int | None = Form(default=None),
        user: schema_user.User = Depends(check_manager),
        db: AsyncSession = Depends(get_db)
):
    expense = await crud_expense.get_expense_by_id(db, expense_id)
    if expense.expense_date != datetime.now(UTC).date():
        raise HTTPException(
            status_code=400,
            detail="This record is locked and cannot be modified after the expense date."
        )
    expense_details = {
        "amount": amount,
        "description": description
    }
    db_expense = await crud_expense.update_expense(db, expense_id, expense_details)
    return {"detail": "successful"}

