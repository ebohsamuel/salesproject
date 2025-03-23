from pydantic import BaseModel
from datetime import date, datetime


class PurchaseBase(BaseModel):
    purchase_date: date
    Quantity: int
    unit_cost: float
    total_cost: float
    product_id: int


class PurchaseCreate(PurchaseBase):
    pass


class Purchase(PurchaseBase):
    id: int

    class ConfigDict:
        from_attributes = True
