from fastapi import Request, Depends
from app.authentication import get_db, get_current_active_user
from app.authentication import template
from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import crud_purchase
from app.schema import schema_user

router = APIRouter(dependencies=[Depends(get_current_active_user)])


@router.get("/purchase-report")
async def purchase_report(
        request: Request,
        db: AsyncSession = Depends(get_db),
        user: schema_user.User = Depends(get_current_active_user)
):
    purchases = await crud_purchase.get_all_purchase(db)
    return template.TemplateResponse(
        "purchase-report.html",
        {"request": request, "purchases": purchases, "full_name": user.fullname}
    )
