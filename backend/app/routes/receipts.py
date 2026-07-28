import base64
import json
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.models.receipt import ReceiptOut, ReceiptUploadResponse
from app.services.ocr_service import extract_receipt_data
from app.services.receipt_validation import validate_receipt
from app.services.receipt_verification import crop_to_bounding_box, verify_is_receipt
from app.utils.paths import EXTRACTED_JSON_DIR, RECEIPTS_DIR
from database.database import get_db
from database.models import Receipt

router = APIRouter(prefix="/receipts", tags=["receipts"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}


# ---------------------------------------------------------------------------
# POST /receipts
# Verify receipt using AI, save uploaded file and create Receipt row.
# ---------------------------------------------------------------------------
@router.post("", status_code=201, response_model=ReceiptUploadResponse)
async def upload_receipt(
    receipt: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if receipt.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only JPG, PNG, WebP and PDF are accepted.",
        )

    # Read uploaded file into memory
    file_bytes = await receipt.read()

    # Verify that the uploaded image is actually a receipt
    verification = verify_is_receipt(
        image_base64=base64.b64encode(file_bytes).decode("utf-8"),
        content_type=receipt.content_type,
    )

    if not verification.get("is_receipt"):
        raise HTTPException(
            status_code=400,
            detail=verification.get(
                "reason",
                "Uploaded file is not a valid receipt.",
            ),
        )

    # Reset the file pointer before saving
    receipt.file.seek(0)

    extension = Path(receipt.filename).suffix
    filename = f"{uuid.uuid4().hex}{extension}"
    dest = RECEIPTS_DIR / filename

    with dest.open("wb") as f:
        shutil.copyfileobj(receipt.file, f)

    crop_to_bounding_box(dest, verification.get("bounding_box"))

    merchant = None
    purchase_date = None
    total = None
    currency = None
    status = "Uploaded"

    try:
        extracted_data = extract_receipt_data(dest)
        if extracted_data:
            validated = validate_receipt(extracted_data)

            json_path = EXTRACTED_JSON_DIR / f"{Path(filename).stem}.json"
            json_path.write_text(json.dumps(validated.model_dump(), indent=2))

            merchant = validated.merchant
            total = validated.total
            currency = validated.currency
            status = "Processed"

            if validated.purchase_date:
                purchase_date = datetime.strptime(validated.purchase_date, "%Y-%m-%d")
    except Exception as exc:
        print(f"OCR extraction failed for {filename}: {exc}")

    receipt_record = Receipt(
        filename=filename,
        image_path=f"uploads/receipts/{filename}",
        merchant=merchant,
        purchase_date=purchase_date,
        total=total,
        currency=currency,
        status=status,
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