from fastapi import APIRouter, Request, Depends
from app.schema import schema_user
from app.authentication import template, get_current_active_user

router = APIRouter(dependencies=[Depends(get_current_active_user)])


@router.get("/dashboard")
async def welcome(request: Request, user: schema_user.User = Depends(get_current_active_user)):
    return template.TemplateResponse("dashboard.html", {"request": request, "full_name": user.fullname})


@router.get("/stock-alert")
async def stock_alert(request: Request, user: schema_user.User = Depends(get_current_active_user)):
    return template.TemplateResponse("stock-alert.html", {"request": request, "full_name": user.fullname})
