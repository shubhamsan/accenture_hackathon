from services.ocr_service import extract_receipt

image_path = image_path = "uploads/receipts/6068a9de796f423f91b959bacedecd49.jpg"

result = extract_receipt(image_path)

print(result)