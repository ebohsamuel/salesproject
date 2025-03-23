import asyncio
from datetime import date
from sqlalchemy.exc import SQLAlchemyError
from app.schema import schema_purchase, schema_stock, schema_user
from fastapi import Request, Depends
from app.authentication import get_db, check_manager, get_current_active_user
from app.authentication import template
from fastapi import APIRouter, Form
from sqlalchemy.ext.asyncio import AsyncSession
from base64 import b64encode
from app.crud import crud_product, crud_stock, crud_purchase

router = APIRouter(dependencies=[Depends(get_current_active_user)])


@router.get("/purchase/add")
async def product_list(
        request: Request,
        db: AsyncSession = Depends(get_db),
        user: schema_user.User = Depends(get_current_active_user)
):
    products = await crud_product.get_all_product(db)

    render_products = []
    for product in products:
        image_data = b64encode(product.image_data).decode() if product.image_data else ""
        render_products.append({
            "id": product.id,
            "image_data": image_data,
            "product_name": product.product_name
        })
        await asyncio.sleep(0)
    return template.TemplateResponse(
        "purchase-add.html",
        {"request": request, "products": render_products, "full_name": user.fullname}
    )


@router.post("/purchase-add")
async def enter_new_purchase(
        product_id: int = Form(),
        purchase_date: date = Form(),
        product_name: str = Form(),
        quantity: int = Form(),
        unit_cost: float = Form(),
        total_cost: float = Form(),
        alert_balance: int | None = Form(default=None),
        user: schema_user.User = Depends(check_manager),
        db: AsyncSession = Depends(get_db)
):

    purchase = schema_purchase.PurchaseCreate(
        purchase_date=purchase_date,
        Quantity=quantity,
        product_id=product_id,
        unit_cost=unit_cost,
        total_cost=total_cost
    )

    try:
        db_purchase = crud_purchase.add_new_purchase(db, purchase)

        # we are going to use this same endpoint to enter our stock table
        db_stock = await crud_stock.get_stock_by_product_id(db, product_id)
        if db_stock:
            db_stock.available_stock += quantity
            if alert_balance:
                db_stock.alert_balance = alert_balance
        else:
            if not alert_balance:
                alert_balance = 5

            stock = schema_stock.StockCreate(
                product_id=product_id,
                available_stock=quantity,
                alert_balance=alert_balance
            )
            db_stock = crud_stock.add_new_stock(db, stock)

        await db.commit()
        await db.refresh(db_stock)
        await db.refresh(db_purchase)

        return {"detail": " purchase and stock added successfully"}
    except SQLAlchemyError as e:
        await db.rollback()
        print(f"An error occurred: {e}")
        raise
    except ValueError as e:
        await db.rollback()
        raise
