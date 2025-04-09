import asyncio
from datetime import datetime, UTC
from sqlalchemy.exc import SQLAlchemyError
from app.crud import crud_sale, crud_product, crud_stock
from fastapi import Request, Depends, HTTPException
from app.authentication import get_db, template, check_manager, get_current_active_user
from fastapi import APIRouter, Form
from sqlalchemy.ext.asyncio import AsyncSession
from app.schema import schema_user


router = APIRouter(dependencies=[Depends(get_current_active_user)])


@router.get("/sales-update")
async def sales_update(
        request: Request,
        db: AsyncSession = Depends(get_db),
        user: schema_user.User = Depends(get_current_active_user)
):
    order_items = await crud_sale.get_all_order_item(db)
    return template.TemplateResponse(
        "sales-update.html",
        {"request": request, "order_items": order_items, "full_name": user.fullname}
    )


@router.get("/sales-data")
async def sales_list(date_str: str, db: AsyncSession = Depends(get_db)):
    sales = await crud_sale.get_order_item_by_order_date(db, date_str)
    items = []
    for item in sales:
        items.append({
            "id": item.id,
            "order_date": item.order.order_date,
            "product_name": item.product.product_name,
            "user": item.order.user.fullname,
            "customer_name": item.order.customer_name,
            "quantity": item.quantity,
            "payment_method": item.order.payment_method,
            "price": item.price,
            "order_id": item.order_id
        })
        await asyncio.sleep(0)

    return {"data": items}


@router.get("/sales-filter")
async def sales_list(start_date: str, end_date: str, db: AsyncSession = Depends(get_db)):
    sales = await crud_sale.get_order_item_between_order_date(db, start_date, end_date)
    items = []
    for item in sales:
        items.append({
            "id": item.id,
            "order_date": item.order.order_date,
            "product_name": item.product.product_name,
            "user": item.order.user.fullname,
            "customer_name": item.order.customer_name,
            "quantity": item.quantity,
            "payment_method": item.order.payment_method,
            "price": item.price,
            "order_id": item.order_id
        })
        await asyncio.sleep(0)

    return {"data": items}


@router.post("/sales/update")
async def sales_update_submit(
        order_item_id: int = Form(),
        order_id: int = Form(),
        quantity: int | None = Form(default=None),
        product_name: str | None = Form(default=None),
        user: schema_user.User = Depends(check_manager),
        db: AsyncSession = Depends(get_db)
):
    try:
        order = await crud_sale.get_order_by_id(db, order_id)
        if order.order_date != datetime.now(UTC).date():
            raise HTTPException(
                status_code=400,
                detail="This record is locked and cannot be modified after the order date."
            )
        order_item = await crud_sale.get_order_item_by_id(db, order_item_id)
        wrong_stock = None
        right_stock = None

        if product_name:
            product_name = product_name.strip().lower()
            db_product = await crud_product.get_product_by_product_name(db, product_name)
            if not db_product:
                raise HTTPException(status_code=400, detail="Product does not exists")

            if quantity is None:

                # correcting the stock table
                wrong_stock = await crud_stock.get_stock_by_product_id(db, order_item.product_id)
                wrong_stock.available_stock += order_item.quantity

                right_stock = await crud_stock.get_stock_by_product_id(db, db_product.id)
                right_stock.available_stock -= order_item.quantity

                # Check if there is enough stock available to replace the previously selected product
                if right_stock.available_stock < 0:
                    raise HTTPException(status_code=400, detail="Not enough quantity for this product")

                # correcting the order table
                wrong_amount = order_item.price * order_item.quantity
                right_amount = right_stock.price * order_item.quantity
                order.total_amount = order.total_amount - wrong_amount + right_amount

                # correcting the order item table
                order_item.product_id = db_product.id
                order_item.price = right_stock.price

            else:
                # correcting the stock table
                wrong_stock = await crud_stock.get_stock_by_product_id(db, order_item.product_id)
                wrong_stock.available_stock += order_item.quantity

                right_stock = await crud_stock.get_stock_by_product_id(db, db_product.id)
                right_stock.available_stock -= quantity

                # Check if there is enough stock available to replace the previously selected product
                if right_stock.available_stock < 0:
                    raise HTTPException(status_code=400, detail="Not enough quantity for this product")

                # correcting the order table
                wrong_amount = order_item.price * order_item.quantity
                right_amount = right_stock.price * quantity
                order.total_amount = order.total_amount - wrong_amount + right_amount

                # correcting the order item table
                order_item.product_id = db_product.id
                order_item.price = right_stock.price
                order_item.quantity = quantity

        elif quantity:
            # updating stock table
            right_stock = await crud_stock.get_stock_by_product_id(db, order_item.product_id)
            right_stock.available_stock = right_stock.available_stock + order_item.quantity - quantity

            # Check if there is enough stock available to replace the previously selected product
            if right_stock.available_stock < 0:
                raise HTTPException(status_code=400, detail="Not enough quantity for this product")

            # correcting the order table
            wrong_amount = order_item.price * order_item.quantity
            right_amount = right_stock.price * quantity # this is to ensure that you update with the latest product price
            order.total_amount = order.total_amount - wrong_amount + right_amount

            # updating order item table
            order_item.quantity = quantity
            order_item.price = right_stock.price  # this is to ensure that you update with the latest product price

        await db.commit()
        await db.refresh(order_item)
        await db.refresh(order)
        if right_stock:
            await db.refresh(right_stock)
        if wrong_stock:
            await db.refresh(wrong_stock)

        return {"detail": "update successful"}

    except SQLAlchemyError as e:
        await db.rollback()
        print(f"An error occurred: {e}")
        raise
    except ValueError as e:
        await db.rollback()
        raise
