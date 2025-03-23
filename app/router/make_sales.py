from base64 import b64encode
from fastapi import Request, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from app.authentication import get_db, get_current_active_user
from app.authentication import template
from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import crud_product, crud_stock, crud_user, crud_sale
from app.schema import schema_user
from app.schema.schema_sale import Data

router = APIRouter(dependencies=[Depends(get_current_active_user)])


@router.get("/sales")
async def sales(request: Request, db: AsyncSession = Depends(get_db)):
    products = await crud_product.get_all_product(db)
    render_products = []
    for product in products:
        db_stock = await crud_stock.get_stock_by_product_id(db, product_id=product.id)
        if db_stock:
            image_data = b64encode(product.image_data).decode() if product.image_data else ""
            render_products.append({
                "id": product.id,
                "image_data": image_data,
                "product_name": product.product_name,
                "price": product.stock.price,
                "available": product.stock.available_stock
            })
    return template.TemplateResponse("sales.html", {"request": request, "products": render_products})


@router.get("/sales-summary")
async def sales_summary(request: Request, user: schema_user.User = Depends(get_current_active_user)):
    return template.TemplateResponse("sales-summary.html", {"request": request, "email": user.email})


@router.post("/sales/add")
async def add_sales(data: Data, db: AsyncSession = Depends(get_db)):
    order = data.order
    items = data.items

    # before registering sales, we are going to check if the quantities paid for by customers are available in stock
    for item in items:
        product = await crud_product.get_product_by_product_name(db, item.product_name)

        stock = await crud_stock.get_stock_by_product_id(db, product.id)

        if stock.available_stock < item.quantity:
            raise HTTPException(
                status_code=400,
                detail="Cannot proceed with the transaction because of lack of stock. Please cancel transaction"
            )
        if stock.price != item.price:
            raise HTTPException(
                status_code=400,
                detail="Cannot proceed with the transaction because of change in price. Please cancel transaction"
            )

    # if there are stocks available for sales and there are no price difference, then proceed with the sales
    user = await crud_user.get_user_by_email(db, order.user_email)
    order = order.model_dump(exclude_none=True)
    order.pop("user_email")
    db_order = await crud_sale.create_new_order(db, order, user_id=user.id)
    order_id = db_order.id
    db_order_item = None
    db_stock = None
    try:
        for item in items:
            db_product = await crud_product.get_product_by_product_name(db, item.product_name)
            product_id = db_product.id
            item = item.model_dump()
            item.pop("product_name")
            db_stock = await crud_stock.get_stock_by_product_id(db, product_id)
            db_order_item = crud_sale.create_new_order_item(db, item, order_id, product_id)
            db_stock.available_stock -= item.get("quantity")

        await db.commit()

        if db_order_item:
            await db.refresh(db_order_item)
        if db_stock:
            await db.refresh(db_stock)

        return {"detail": "sales recorded successfully", "receipt": db_order.id}
    except SQLAlchemyError as e:
        await db.rollback()
        print(f"An error occurred: {e}")
        raise
    except ValueError as e:
        await db.rollback()
        raise
