from datetime import datetime

from app.models.receipt import ExtractedReceipt

SUPPORTED_CURRENCIES = {
    "GBP",
    "USD",
    "EUR",
    "INR",
    "AUD",
    "CAD",
}


def validate_receipt(receipt_data: dict) -> ExtractedReceipt:
    """
    Validate and clean OCR output before saving to the database.
    """

    receipt = ExtractedReceipt(**receipt_data)

    if receipt.merchant:
        receipt.merchant = receipt.merchant.strip()

    if receipt.currency:
        receipt.currency = receipt.currency.upper()

        if receipt.currency not in SUPPORTED_CURRENCIES:
            receipt.currency = None

    if receipt.purchase_date:
        try:
            parsed = datetime.strptime(receipt.purchase_date, "%Y-%m-%d")
            receipt.purchase_date = parsed.strftime("%Y-%m-%d")
        except ValueError:
            receipt.purchase_date = None

    return receipt
