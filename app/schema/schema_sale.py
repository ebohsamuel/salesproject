from datetime import date

from pydantic import BaseModel


class Detail(BaseModel):
    order_date: date
    total_amount: float
    user_email: str
    customer_email: str | None = None
    customer_name: str | None = None
    payment_method: str | None = None


class Item(BaseModel):
    product_name: str
    price: float
    quantity: int


class Data(BaseModel):
    order: Detail
    items: list[Item]
