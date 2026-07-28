from typing import Optional

from pydantic import BaseModel


class ReceiptItem(BaseModel):
    name: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    total_price: Optional[float] = None
    category: Optional[str] = None


class Receipt(BaseModel):
    merchant: Optional[str] = None
    purchase_date: Optional[str] = None
    currency: Optional[str] = None
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total: Optional[float] = None
    payment_method: Optional[str] = None
    items: list[ReceiptItem] = []