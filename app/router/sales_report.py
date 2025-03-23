from app.crud import crud_sale
from fastapi import Request, Depends
from app.authentication import get_db, template, get_current_active_user
from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(dependencies=[Depends(get_current_active_user)])


@router.get("/sales-report")
async def sales_report(request: Request, db: AsyncSession = Depends(get_db)):
    order_items = await crud_sale.get_all_order_item(db)
    return template.TemplateResponse("sales-report.html", {"request": request, "order_items": order_items})