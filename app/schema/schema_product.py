from pydantic import BaseModel


class ProductBase(BaseModel):
    product_name: str
    image_data: bytes | None


class ProductCreate(ProductBase):
    pass


class ProductCategory(ProductBase):
    id: int

    class ConfigDict:
        from_attributes = True
