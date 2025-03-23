from datetime import date
from pydantic import BaseModel


class ExpenseBase(BaseModel):
    expense_date: date | None = None
    description: str | None = None
    amount: int | None = None


class ExpenseCreate(ExpenseBase):
    pass


class Expense(ExpenseBase):
    id: int

    class ConfigDict:
        from_attributes = True
