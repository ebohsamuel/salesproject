from sqlalchemy.ext.asyncio import AsyncSession
from app.schema import schema_user
from app.crud import crud_user
from fastapi import Depends, APIRouter, Form, HTTPException
from app.authentication import get_db, check_manager, get_current_active_user

router = APIRouter(dependencies=[Depends(get_current_active_user)])


@router.post("/user-add")
async def add_new_user(
        email: str = Form(),
        password: str = Form(),
        fullname: str = Form(),
        user_category: str = Form(),
        phone: str = Form(),
        address: str | None = Form(default=None),
        next_of_kin: str | None = Form(default=None),
        phone_next_of_kin: str | None = Form(default=None),
        user: schema_user.User = Depends(check_manager),
        db: AsyncSession = Depends(get_db)
):
    email = email.strip().lower()
    check_user = await crud_user.get_user_by_email(db, email)
    if check_user:
        raise HTTPException(status_code=400, detail="user already exist")
    if next_of_kin:
        next_of_kin = next_of_kin.lower().strip()
    if address:
        address = address.lower().strip()
    user = schema_user.UserCreate(
        email=email,
        password=password,
        fullname=fullname.lower(),
        user_category=user_category,
        phone=phone,
        address=address,
        next_of_kin=next_of_kin,
        phone_next_of_kin=phone_next_of_kin
    )

    db_user = await crud_user.create_user(db, user)
    return {'detail': 'successful!'}
