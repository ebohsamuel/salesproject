from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.authentication import get_db, template, get_current_active_user
from app.crud import crud_expense


router = APIRouter(dependencies=[Depends(get_current_active_user)])


@router.get("/expense-report")
async def expense_report(request: Request, db: AsyncSession = Depends(get_db)):
    expenses = await crud_expense.get_expenses(db)
    return template.TemplateResponse("expenses-report.html", {"request": request, "expenses": expenses})