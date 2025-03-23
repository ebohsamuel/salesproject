from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import crud_user
from fastapi import Depends, APIRouter, Form, Request, HTTPException
from app.authentication import get_db, template, check_manager, get_current_active_user
from app.schema import schema_user

router = APIRouter(dependencies=[Depends(get_current_active_user)])


@router.get("/user")
async def user_data(request: Request, db: AsyncSession = Depends(get_db)):
    users = await crud_user.get_users(db)
    return template.TemplateResponse("user.html", {"request": request, "users": users})


@router.post("/user-update")
async def user_update(
        user_id: int = Form(),
        email: str | None = Form(default=None),
        is_active: bool | None = Form(default=None),
        password: str | None = Form(default=None),
        fullname: str | None = Form(default=None),
        user_category: str | None = Form(default=None),
        phone: str | None = Form(default=None),
        address: str | None = Form(default=None),
        next_of_kin: str | None = Form(default=None),
        phone_next_of_kin: str | None = Form(default=None),
        user: schema_user.User = Depends(check_manager),
        db: AsyncSession = Depends(get_db)
):

    if fullname:
        fullname = fullname.lower().strip()
    if next_of_kin:
        next_of_kin = next_of_kin.lower().strip()
    if address:
        address = address.lower().strip()
    if email:
        email = email.strip().lower()
        check_user = await crud_user.get_user_by_email(db, email)
        if check_user:
            raise HTTPException(status_code=400, detail="user already exist")

    user_details = {
        "email": email,
        "is_active": is_active,
        "password": password,
        "fullname": fullname,
        "user_category": user_category,
        "phone": phone,
        "address": address,
        "next_of_kin": next_of_kin,
        "phone_next_of_kin": phone_next_of_kin
    }

    db_user = await crud_user.update_user(db, user_details, user_id)
    return {'detail': 'successful!'}
