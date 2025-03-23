from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.authentication import get_db, template, get_current_active_user
from app.crud import crud_expense
from app.schema import schema_user

router = APIRouter(dependencies=[Depends(get_current_active_user)])


@router.get("/expense-report")
async def expense_report(
        request: Request,
        db: AsyncSession = Depends(get_db),
        user: schema_user.User = Depends(get_current_active_user)
):
    expenses = await crud_expense.get_expenses(db)
    return template.TemplateResponse(
        "expenses-report.html",
        {"request": request, "expenses": expenses, "full_name": user.fullname}
    )
