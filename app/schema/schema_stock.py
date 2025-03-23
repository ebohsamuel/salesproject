from pydantic import BaseModel


class StockBase(BaseModel):
    price: float | None = None
    product_id: int
    available_stock:int
    alert_balance: int


class StockCreate(StockBase):
    pass


class Stock(StockBase):
    id: int

    class ConfigDict:
        from_attributes = True
