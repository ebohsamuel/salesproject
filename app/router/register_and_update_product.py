import asyncio
from fastapi import Request, Depends, HTTPException
from app.authentication import get_db, get_current_active_user
from app.authentication import template, check_manager
from fastapi import APIRouter, Form, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from base64 import b64encode
from app.crud import crud_product
from app.schema import schema_product, schema_user

router = APIRouter(dependencies=[Depends(get_current_active_user)])


@router.post("/product/add")
async def enter_new_product(
        product_name: str = Form(),
        image_data: UploadFile | None = File(default=None),
        user: schema_user.User = Depends(check_manager),
        db: AsyncSession = Depends(get_db)
):
    product_name = product_name.strip().lower()

    db_product = await crud_product.get_product_by_product_name(db, product_name)

    if db_product:
        raise HTTPException(status_code=400, detail="Product name already exists")
    if image_data:
        image_data = await image_data.read()

    product = schema_product.ProductCreate(
        product_name=product_name,
        image_data=image_data
    )
    db_product = await crud_product.add_new_product(db, product)

    return {"detail": "product registration successful"}


@router.get("/product")
async def product_(
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
        "product.html",
        {"request": request, "products": render_products, "full_name": user.fullname}
    )


@router.post("/product/update")
async def update(
        product_id: int = Form(),
        product_name: str | None = Form(default=None),
        image_data: UploadFile | None = File(default=None),
        user: schema_user.User = Depends(check_manager),
        db: AsyncSession = Depends(get_db)
):
    if image_data:
        image_data = await image_data.read()
    if product_name:
        product_name = product_name.strip().lower()

        db_product = await crud_product.get_product_by_product_name(db, product_name)

        if db_product:
            raise HTTPException(status_code=400, detail="Product name already exists")

    product_details = {
        "image_data": image_data,
        "product_name": product_name
    }

    db_product = await crud_product.update_product(db, product_details, product_id)
    return {"detail": "product update successful"}
