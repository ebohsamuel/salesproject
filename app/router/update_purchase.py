import asyncio
from datetime import date, datetime, UTC
from sqlalchemy.exc import SQLAlchemyError
from app.schema import schema_stock, schema_user
from fastapi import Request, Depends, HTTPException
from app.authentication import get_db, check_manager, get_current_active_user
from app.authentication import template
from fastapi import APIRouter, Form
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import crud_stock, crud_purchase, crud_product

router = APIRouter(dependencies=[Depends(get_current_active_user)])


@router.get("/purchase-update")
async def purchase_update(
        request: Request,
        db: AsyncSession = Depends(get_db),
        user: schema_user.User = Depends(get_current_active_user)
):
    purchases = await crud_purchase.get_all_purchase(db)
    return template.TemplateResponse(
        "purchase-update.html",
        {"request": request, "purchases": purchases, "full_name": user.fullname}
    )


@router.get("/purchase-data")
async def purchase_list(date_str: str, db: AsyncSession = Depends(get_db)):
    purchases = await crud_purchase.get_purchase_by_date(db, date_str)
    purchases_ = []
    for purchase in purchases:
        purchases_.append({
            "id": purchase.id,
            "purchase_date": purchase.purchase_date,
            "product_name": purchase.product.product_name,
            "Quantity": purchase.Quantity,
            "unit_cost": purchase.unit_cost,
            "total_cost": purchase.total_cost
        })
        await asyncio.sleep(0)

    return {"data": purchases_}


@router.post("/purchase/update")
async def purchase_update_submit(
        purchase_id: int = Form(),
        product_name: str | None = Form(default=None),
        purchase_date: date | None = Form(default=None),
        quantity: int | None = Form(default=None),
        unit_cost: float | None = Form(default=None),
        total_cost: float | None = Form(default=None),
        user: schema_user.User = Depends(check_manager),
        db: AsyncSession = Depends(get_db)
):
    purchase = await crud_purchase.get_purchase_by_id(db, purchase_id)
    if purchase.created_at != datetime.now(UTC).date():
        raise HTTPException(
            status_code=400,
            detail="This record is locked and cannot be modified after the date it was created."
        )
    purchase_details = {
        "Quantity": quantity,
        "unit_cost": unit_cost,
        "total_cost": total_cost,
        "purchase_date": purchase_date
    }
    try:
        db_right_stock = None  # assigning db_right_stock to None incase none of the below conditions prove to be false
        db_wrong_stock = None   # assigning db_wrong_stock to None incase none of the below conditions prove to be false
        # these conditions below are needed for updating the stock table correctly
        if product_name:    # we first check if a new product name is to be updated
            product_name = product_name.strip().lower()
            # we check if the new product name is a registered product and if not an exception is raised
            db_product = await crud_product.get_product_by_product_name(db, product_name)
            if not db_product:
                raise HTTPException(status_code=400, detail="Product does not exists")
            purchase_details.update({"product_id": db_product.id})
            # if the new product name is a registered product, we get then proceed to
            # get the purchase record will want updated
            db_purchase = await crud_purchase.get_purchase_by_id(db, purchase_id)
            # thereafter, we proceed to get the product_id of the product that was initially recorded
            product_id = db_purchase.product_id

            # we then proceed to the stock table to get the stock record
            db_wrong_stock = await crud_stock.get_stock_by_product_id(db, product_id)
            # we thereafter reduce the stock value by the initially purchased quantity
            db_wrong_stock.available_stock = db_wrong_stock.available_stock - db_purchase.Quantity

            if db_wrong_stock.available_stock < 0:
                raise HTTPException(
                    status_code=400,
                    detail="Stock cannot be edited as it would result in a negative balance."
                )

            # these next conditions are for when a new quantity is given or not
            if quantity:    # this condition runs when a new quantity is given
                # we proceed to adding a new stock
                # we check if the product id already existed in the stock table
                db_right_stock = await crud_stock.get_stock_by_product_id(db, db_product.id)
                # if it does, we just increase the available stock
                if db_right_stock:
                    db_right_stock.available_stock += quantity
                else:
                    # if the product id does not exist in the stock table, we create a new stock
                    # setting the default value to 5, which can be changed later from
                    # updating stock which is different from this process being discussed
                    alert_balance = 5
                    stock = schema_stock.StockCreate(
                        product_id=db_product.id,
                        available_stock=quantity,
                        alert_balance=alert_balance
                    )
                    db_right_stock = crud_stock.add_new_stock(db, stock)

            # this runs when a new quantity is not given, therefore we create
            # a new stock with the old quantity from the initially recorded purchase
            else:
                quantity = db_purchase.Quantity  # passing the old quantity to use for creating stock

                # we check if the product id already existed in the stock table
                db_right_stock = await crud_stock.get_stock_by_product_id(db, db_product.id)
                # if it does, we just increase the available stock
                if db_right_stock:
                    db_right_stock.available_stock += quantity
                else:
                    # if the product id does not exist in the stock table, we create a new stock
                    # setting the default value to 5, which can be changed later from
                    # updating stock which is different from this process being discussed
                    alert_balance = 5

                    stock = schema_stock.StockCreate(
                        product_id=db_product.id,
                        available_stock=quantity,
                        alert_balance=alert_balance
                    )
                    db_right_stock = crud_stock.add_new_stock(db, stock)
        elif quantity:  # this runs if only the quantity was given, meaning the product id is not changing
            # we get the purchase record from the purchase table
            db_purchase = await crud_purchase.get_purchase_by_id(db, purchase_id)
            # we get the product_id of the product of the purchase record
            product_id = db_purchase.product_id
            # we used the product product_id to get the stock record
            db_right_stock = await crud_stock.get_stock_by_product_id(db, product_id)
            # we updated the stock balance using the provided quantity
            db_right_stock.available_stock = db_right_stock.available_stock - db_purchase.Quantity + quantity

        db_purchase_update = await crud_purchase.update_purchase(db, purchase_details, purchase_id)

        await db.commit()
        await db.refresh(db_purchase_update)
        if db_right_stock:
            await db.refresh(db_right_stock)
        if db_wrong_stock:
            await db.refresh(db_wrong_stock)

        return {"detail": "update successful"}
    except SQLAlchemyError as e:
        await db.rollback()
        print(f"An error occurred: {e}")
        raise
    except ValueError as e:
        await db.rollback()
        raise
