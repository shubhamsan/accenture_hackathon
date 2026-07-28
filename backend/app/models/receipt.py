from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReceiptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    image_path: str
    merchant: str | None = None
    purchase_date: datetime | None = None
    total: float | None = None
    currency: str | None = None
    status: str
    created_at: datetime


class ReceiptUploadResponse(BaseModel):
    message: str
    receipt_id: int
    filename: str
