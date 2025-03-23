from fastapi import Request, Depends
from app.authentication import get_db, check_manager, get_current_active_user
from app.authentication import template
from fastapi import APIRouter, Form
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import crud_stock, crud_product
from app.schema import schema_user

router = APIRouter()


@router.get("/stock")
async def stock(
        request: Request,
        db: AsyncSession = Depends(get_db),
        user: schema_user.User = Depends(get_current_active_user)
):
    stocks = await crud_stock.get_all_stocks(db)
    return template.TemplateResponse("stock.html", {"request": request, "stocks": stocks, "full_name": user.fullname})


@router.post("/stock/update")
async def stock_update(
        product_name: str = Form(),
        price: float | None = Form(default=None),
        alert_balance: int | None = Form(default=None),
        user: schema_user.User = Depends(check_manager),
        db: AsyncSession = Depends(get_db)
):
    stock_details = {
        "price": price,
        "alert_balance": alert_balance
    }

    product = await crud_product.get_product_by_product_name(db, product_name)

    db_stock = await crud_stock.update_stock(db, stock_details, product.id)
    return {"detail": "stock update successful"}
