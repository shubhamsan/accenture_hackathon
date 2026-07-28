import base64
import json
import os
import shutil
import time
from pathlib import Path

import cv2
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI(title="Receipts to Riches API")

UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}

DATA_FILE = Path("receipts_data.json")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def crop_to_bounding_box(image_path: Path, bounding_box: dict, padding_frac: float = 0.03) -> bool:
    """Crop the saved image to a normalized (0-1) bounding box, with a little padding.

    Returns True if a crop was applied, False if the box was missing/invalid
    (in which case the original image is left untouched).
    """
    if not bounding_box:
        return False

    try:
        x_min, y_min, x_max, y_max = (
            float(bounding_box["x_min"]),
            float(bounding_box["y_min"]),
            float(bounding_box["x_max"]),
            float(bounding_box["y_max"]),
        )
    except (KeyError, TypeError, ValueError):
        return False

    if not (0 <= x_min < x_max <= 1 and 0 <= y_min < y_max <= 1):
        return False

    image = cv2.imread(str(image_path))
    if image is None:
        return False  # not a decodable image

    height, width = image.shape[:2]
    pad_x = (x_max - x_min) * padding_frac
    pad_y = (y_max - y_min) * padding_frac

    left = max(0, int((x_min - pad_x) * width))
    top = max(0, int((y_min - pad_y) * height))
    right = min(width, int((x_max + pad_x) * width))
    bottom = min(height, int((y_max + pad_y) * height))

    if right - left < 10 or bottom - top < 10:
        return False  # degenerate box, keep the original

    cv2.imwrite(str(image_path), image[top:bottom, left:right])
    return True


def load_receipts() -> list:
    """Simple JSON-file 'database' of extracted receipt data. Swap this out
    for a real DB query once you have one."""
    if not DATA_FILE.exists():
        return []
    return json.loads(DATA_FILE.read_text())


def save_receipt(filename: str, data: dict) -> None:
    receipts = load_receipts()
    receipts.append({"filename": filename, **data})
    DATA_FILE.write_text(json.dumps(receipts, indent=2))


def _parse_json_response(raw_content: str) -> dict:
    """Strip markdown code fences (if any) and parse the model's JSON reply."""
    raw_content = raw_content.strip()
    if raw_content.startswith("```"):
        raw_content = raw_content.strip("`")
        if raw_content.startswith("json"):
            raw_content = raw_content[4:]
        raw_content = raw_content.strip()
    return json.loads(raw_content)


def verify_is_receipt(image_base64: str, content_type: str) -> dict:
    """Dedicated classification call: is this image actually a receipt/invoice?

    Kept separate from extraction so a non-receipt image is rejected with a
    cheap, focused call before we spend tokens trying to extract line items
    from e.g. a selfie or a screenshot. When it is a receipt, also asks for a
    tight bounding box so the image can be auto-cropped before extraction.
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Look at this image. Is it a photo or scan of a purchase "
                        "receipt, invoice, or bill (something showing a store/vendor, "
                        "purchased items or services, and a total amount)? "
                        "Respond with ONLY JSON in this exact shape: "
                        '{"is_receipt": true|false, "reason": "short explanation", '
                        '"bounding_box": {"x_min": 0-1, "y_min": 0-1, "x_max": 0-1, "y_max": 0-1}}. '
                        "bounding_box should tightly frame just the receipt/document itself "
                        "(as a fraction of image width/height) when is_receipt is true; "
                        "set it to null when is_receipt is false."
                    ),
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{content_type};base64,{image_base64}"},
                },
            ],
        }],
        max_tokens=200,
    )
    return _parse_json_response(response.choices[0].message.content)


def extract_receipt_data(image_base64: str, content_type: str) -> dict:
    """Ask GPT-4o Vision to extract structured fields from a verified receipt."""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Extract the following from this receipt and return as JSON: store_name, date, items (list of {name, price}), total_amount, category (e.g. groceries, dining, transport).",
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{content_type};base64,{image_base64}"},
                },
            ],
        }],
    )
    return _parse_json_response(response.choices[0].message.content)


# ---------------------------------------------------------------------------
# POST /receipts
# Accepts a file upload, verifies it's actually a receipt, and saves it to
# the /uploads directory.
# ---------------------------------------------------------------------------
@app.post("/receipts", status_code=201)
async def upload_receipt(receipt: UploadFile = File(...)):
    if receipt.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only JPG, PNG, WebP and PDF are accepted.",
        )

    filename = f"{int(time.time() * 1000)}-{receipt.filename}"
    dest = UPLOADS_DIR / filename

    with dest.open("wb") as f:
        shutil.copyfileobj(receipt.file, f)

    image_base64 = base64.b64encode(dest.read_bytes()).decode()

    # GPT-4o Vision can only "see" image content types — PDFs are skipped here
    # and go straight to extraction, same as before.
    if receipt.content_type != "application/pdf":
        verification = verify_is_receipt(image_base64, receipt.content_type)
        if not verification.get("is_receipt"):
            dest.unlink(missing_ok=True)
            raise HTTPException(
                status_code=422,
                detail=(
                    "Uploaded file does not appear to be a receipt: "
                    f"{verification.get('reason', 'no receipt detected.')}"
                ),
            )

        # Auto-crop to just the receipt using the model's bounding box
        # (no-op if the box is missing/invalid — the original image is kept).
        if crop_to_bounding_box(dest, verification.get("bounding_box")):
            image_base64 = base64.b64encode(dest.read_bytes()).decode()

    receipt_data = extract_receipt_data(image_base64, receipt.content_type)
    print("Extracted receipt data:", receipt_data)

    save_receipt(filename, receipt_data)

    return {"message": "Receipt uploaded successfully.", "filename": filename}


# ---------------------------------------------------------------------------
# GET /receipts
# Returns a list of files currently in /uploads.
# Once you have a database, replace this with a DB query.
# ---------------------------------------------------------------------------
@app.get("/receipts")
def list_receipts():
    extracted_by_filename = {r["filename"]: r for r in load_receipts()}
    files = [
        {
            "filename": f.name,
            "uploaded_at": f.stat().st_mtime,
            **extracted_by_filename.get(f.name, {}),
        }
        for f in UPLOADS_DIR.iterdir()
        if f.is_file()
    ]
    files.sort(key=lambda r: r["uploaded_at"], reverse=True)
    return files


# ---------------------------------------------------------------------------
# GET /insights
# Returns AI-generated spending insights.
# ---------------------------------------------------------------------------
@app.get("/insights")
def get_insights():
    # Step 1 — Fetch all processed receipt data from our JSON "database"
    receipts = load_receipts()
    if not receipts:
        return {
            "message": "No receipts yet — upload some to get insights!",
            "insights": None,
        }

    # Step 2 — Ask GPT to analyse spending patterns across all receipts
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are a personal finance advisor. Analyse the user's spending data and provide clear, actionable insights.",
            },
            {
                "role": "user",
                "content": f"Here is my spending data: {json.dumps(receipts)}. Please provide: 1) a spending summary, 2) top spending categories, 3) three specific saving tips.",
            },
        ],
    )

    # Step 3 — Return the insights to the frontend
    return {"insights": response.choices[0].message.content}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)
