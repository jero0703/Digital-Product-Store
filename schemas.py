
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)


# ============================================================
# USER / AUTH SCHEMAS
# ============================================================

class UserRegister(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100,
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
    )

    role: Literal["USER", "ADMIN"] = "USER"

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Name cannot be empty")

        return value


class UserLogin(BaseModel):
    email: EmailStr

    password: str = Field(
        min_length=1,
        max_length=128,
    )


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: Literal["USER", "ADMIN"]
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ============================================================
# PRODUCT SCHEMAS
# ============================================================

class ProductCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=200,
    )

    description: str = Field(
        min_length=1,
    )

    price: Decimal = Field(
        gt=0,
        max_digits=12,
        decimal_places=2,
    )

    image_url: str | None = Field(
        default=None,
        max_length=500,
    )

    category: str = Field(
        min_length=1,
        max_length=100,
    )

    is_active: bool = True

    @field_validator("name", "description", "category")
    @classmethod
    def clean_text(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Value cannot be empty")

        return value


class ProductUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    description: str | None = Field(
        default=None,
        min_length=1,
    )

    price: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=12,
        decimal_places=2,
    )

    image_url: str | None = Field(
        default=None,
        max_length=500,
    )

    category: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    is_active: bool | None = None

    @field_validator("name", "description", "category")
    @classmethod
    def clean_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError("Value cannot be empty")

        return value


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    price: Decimal
    image_url: str | None
    category: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProductPage(BaseModel):
    items: list[ProductResponse]

    page: int = Field(
        ge=1,
    )

    limit: int = Field(
        ge=1,
        le=100,
    )

    total: int = Field(
        ge=0,
    )

    total_pages: int = Field(
        ge=0,
    )


# ============================================================
# CART SCHEMAS
# ============================================================

class CartItemCreate(BaseModel):
    product_id: int = Field(
        gt=0,
    )

    quantity: int = Field(
        gt=0,
        le=1000,
    )


class CartItemUpdate(BaseModel):
    quantity: int = Field(
        gt=0,
        le=1000,
    )


class CartItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal


class CartResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    items: list[CartItemResponse]
    total_amount: Decimal


# ============================================================
# ORDER SCHEMAS
# ============================================================

class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int | None
    product_name: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    stripe_session_id: str | None
    stripe_payment_intent_id: str | None
    amount: Decimal
    currency: str
    status: str


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    total_amount: Decimal
    status: str
    created_at: datetime
    items: list[OrderItemResponse]
    payment: PaymentResponse | None


class OrderPage(BaseModel):
    items: list[OrderResponse]

    page: int = Field(
        ge=1,
    )

    limit: int = Field(
        ge=1,
        le=100,
    )

    total: int = Field(
        ge=0,
    )

    total_pages: int = Field(
        ge=0,
    )


# ============================================================
# STRIPE CHECKOUT
# ============================================================

class CheckoutSessionResponse(BaseModel):
    order_id: int
    session_id: str
    checkout_url: str


# ============================================================
# ADMIN REPORTS
# ============================================================

class AdminStatsResponse(BaseModel):
    total_products: int
    total_orders: int
    paid_orders: int
    failed_orders: int
    total_revenue: Decimal


class PopularProductReport(BaseModel):
    product_id: int
    product_name: str
    quantity_sold: int
    revenue: Decimal


class OrdersPerUserReport(BaseModel):
    user_id: int
    user_name: str
    order_count: int


class TopCustomerReport(BaseModel):
    user_id: int
    user_name: str
    total_spent: Decimal
