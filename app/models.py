from sqlalchemy import Date, ForeignKey, LargeBinary, func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import date


from app.database import Base


class User(Base):
    __tablename__ = "user"

    id:Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    hashed_password: Mapped[str]
    fullname: Mapped[str]
    phone: Mapped[str] = mapped_column(default=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    user_category: Mapped[str]
    address: Mapped[str] = mapped_column(nullable=True)
    next_of_kin: Mapped[str] = mapped_column(nullable=True)
    phone_next_of_kin: Mapped[str] = mapped_column(nullable=True)

    orders = relationship("Order", back_populates="user")


class Product(Base):
    __tablename__ = "product"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_name: Mapped[str] = mapped_column(unique=True, index=True)
    image_data: Mapped[bytes] = mapped_column(LargeBinary, nullable=True)

    purchases = relationship("Purchase", back_populates="product")
    stock = relationship("Stock", back_populates="product", uselist=False)
    orderitems = relationship("OrderItem", back_populates="product")


class Purchase(Base):
    __tablename__ = "purchase"

    id: Mapped[int] = mapped_column(primary_key=True)
    purchase_date: Mapped[date] = mapped_column(Date)
    product_id: Mapped[int] = mapped_column(ForeignKey("product.id"))
    Quantity: Mapped[int]
    unit_cost: Mapped[float]
    total_cost: Mapped[float]
    created_at: Mapped[date] = mapped_column(Date, server_default=func.current_date(), nullable=True)

    product = relationship("Product", back_populates="purchases")


class Stock(Base):
    __tablename__ = "stock"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("product.id"), unique=True)
    price: Mapped[float] = mapped_column(nullable=True)
    available_stock: Mapped[int]
    alert_balance: Mapped[int]

    product = relationship("Product", back_populates="stock")


class Order(Base):
    __tablename__ = "order"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    order_date: Mapped[date] = mapped_column(Date)
    customer_name: Mapped[str] = mapped_column(nullable=True)
    customer_email: Mapped[str] = mapped_column(nullable=True)
    payment_method: Mapped[str]
    total_amount: Mapped[float]

    user = relationship("User", back_populates="orders")
    orderitems = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "orderitem"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("order.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("product.id"))
    quantity: Mapped[int]
    price: Mapped[float]

    order = relationship("Order", back_populates="orderitems")
    product = relationship("Product", back_populates="orderitems")


class Expense(Base):
    __tablename__ = "expense"

    id: Mapped[int] = mapped_column(primary_key=True)
    expense_date: Mapped[date] = mapped_column(Date, nullable=True)
    description: Mapped[str] = mapped_column(nullable=True)
    amount: Mapped[int] = mapped_column(nullable=True)
