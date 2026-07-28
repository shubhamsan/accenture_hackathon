from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

UPLOADS_DIR = BASE_DIR / "uploads"
RECEIPTS_DIR = UPLOADS_DIR / "receipts"
EXTRACTED_JSON_DIR = UPLOADS_DIR / "extracted_json"

RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
EXTRACTED_JSON_DIR.mkdir(parents=True, exist_ok=True)
