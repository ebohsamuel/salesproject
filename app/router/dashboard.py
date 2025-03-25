import asyncio

from fastapi import Depends, Request
from app.authentication import get_db, template, get_current_active_user
from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import crud_purchase, crud_sale, crud_expense, crud_stock

router = APIRouter(dependencies=[Depends(get_current_active_user)])


@router.get("/dashboard-report")
async def dashboard_report(date_str: str | None = None, db: AsyncSession = Depends(get_db)):
    stocks = await crud_stock.get_stock_with_less_than_alert_balance(db)
    if not date_str:
        purchases = await crud_purchase.get_all_purchase(db)
        orders = await crud_sale.get_all_order(db)
        expenses = await crud_expense.get_expenses(db)
    else:
        purchases = await crud_purchase.get_purchase_by_date(db, date_str)
        orders = await crud_sale.get_order_by_date(db, date_str)
        expenses = await crud_expense.get_expense_by_date(db, date_str)
    purchases_ = []
    for purchase in purchases:
        purchases_.append({
            "id": purchase.id,
            "purchase_date": purchase.purchase_date,
            "product_name": purchase.product.product_name,
            "Quantity": purchase.Quantity,
            "unit_cost": purchase.unit_cost,
            "total_cost": purchase.total_cost,
            "product_id": purchase.product_id
        })
        await asyncio.sleep(0)
    stocks_ = []
    for stock in stocks:
        stocks_.append({
            "product_name": stock.product.product_name,
            "available_stock": stock.available_stock
        })

    return {"purchases": purchases_, "sales": orders, "expenses": expenses, "stock_alert": stocks_}
