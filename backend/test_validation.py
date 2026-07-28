from services.ocr_service import extract_receipt
from services.validation_service import validate_receipt

image_path = "uploads/receipts/6068a9de796f423f91b959bacedecd49.jpg"

ocr_result = extract_receipt(image_path)

validated = validate_receipt(ocr_result)

print(validated.model_dump())