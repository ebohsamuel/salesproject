from pydantic import BaseModel


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str
    fullname: str
    phone: str
    user_category: str
    address: str | None = None
    next_of_kin: str | None = None
    phone_next_of_kin: str | None = None


class User(UserBase):
    id: int
    is_active: bool

    class ConfigDict:
        from_attributes = True
