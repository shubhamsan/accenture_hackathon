import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.models.receipt import ReceiptOut, ReceiptUploadResponse
from app.utils.paths import RECEIPTS_DIR
from database.database import get_db
from database.models import Receipt

router = APIRouter(prefix="/receipts", tags=["receipts"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}


# ---------------------------------------------------------------------------
# POST /receipts
# Saves the uploaded image to uploads/receipts/ and creates a Receipt row.
# OCR extraction (merchant, total, etc.) is added in Phase 2 — see
# app/services/ocr_service.py.
# ---------------------------------------------------------------------------
@router.post("", status_code=201, response_model=ReceiptUploadResponse)
async def upload_receipt(receipt: UploadFile = File(...), db: Session = Depends(get_db)):
    if receipt.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only JPG, PNG, WebP and PDF are accepted.",
        )

    extension = Path(receipt.filename).suffix
    filename = f"{uuid.uuid4().hex}{extension}"
    dest = RECEIPTS_DIR / filename

    with dest.open("wb") as f:
        shutil.copyfileobj(receipt.file, f)

    receipt_record = Receipt(
        filename=filename,
        image_path=f"uploads/receipts/{filename}",
        status="Uploaded",
    )
    db.add(receipt_record)
    db.commit()
    db.refresh(receipt_record)

    return ReceiptUploadResponse(
        message="Receipt uploaded successfully.",
        receipt_id=receipt_record.id,
        filename=filename,
    )


# ---------------------------------------------------------------------------
# GET /receipts
# Returns all receipt records from the database, newest first.
# ---------------------------------------------------------------------------
@router.get("", response_model=list[ReceiptOut])
def list_receipts(db: Session = Depends(get_db)):
    return db.query(Receipt).order_by(Receipt.created_at.desc()).all()
