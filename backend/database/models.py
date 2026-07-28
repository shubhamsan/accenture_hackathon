from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String

from database.database import Base


class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    image_path = Column(String, nullable=False)
    merchant = Column(String, nullable=True)
    purchase_date = Column(DateTime, nullable=True)
    total = Column(Float, nullable=True)
    currency = Column(String, nullable=True)
    status = Column(String, nullable=False, default="Uploaded")
    created_at = Column(DateTime, default=datetime.utcnow)
