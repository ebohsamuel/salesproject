from fastapi import FastAPI, Request, Depends
from app.authentication import template, get_db, get_current_active_user
from app.crud import crud_user
from app.router import register_and_update_product, new_purchase_and_stock, update_purchase, update_stock, make_sales
from app.router import update_sales, new_expense, update_expense, purchase_report, sales_report, expense_report
from app.router import dashboard, create_user, update_user, login, navigation, logout
from app.database import async_engine, Base
from app.schema import schema_user
import os

app = FastAPI()

app.include_router(register_and_update_product.router)
app.include_router(new_purchase_and_stock.router)
app.include_router(update_purchase.router)
app.include_router(update_stock.router)
app.include_router(make_sales.router)
app.include_router(update_sales.router)
app.include_router(new_expense.router)
app.include_router(update_expense.router)
app.include_router(purchase_report.router)
app.include_router(sales_report.router)
app.include_router(expense_report.router)
app.include_router(dashboard.router)
app.include_router(create_user.router)
app.include_router(update_user.router)
app.include_router(login.router)
app.include_router(navigation.router)
app.include_router(logout.router)

admin_email = os.getenv("admin_email")
admin_password = os.getenv("admin_password")
user_category = os.getenv("user_category")
phone = os.getenv("phone")
fullname = os.getenv("fullname")


@app.on_event("startup")
async def on_startup():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    db_generator = get_db()
    db = await anext(db_generator)
    try:
        data = {
            "email": f"{admin_email}",
            "password": f"{admin_password}",
            "user_category": f"{user_category}",
            "phone": f"{phone}",
            "fullname": f"{fullname}"
        }
        schema_data = schema_user.UserCreate(**data)

        db_user = await crud_user.get_user_by_email(db, email=schema_data.email)
        if not db_user:
            user = await crud_user.create_user(db=db, user=schema_data)
            print("Admin user created.")
        else:
            print("Admin user already exists.")
    finally:
        await db_generator.aclose()


@app.get("/")
async def login(request: Request):
    return template.TemplateResponse("login.html", {"request": request})
