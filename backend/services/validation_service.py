from datetime import datetime

from models.receipt_model import Receipt


SUPPORTED_CURRENCIES = {
    "GBP",
    "USD",
    "EUR",
    "INR",
    "AUD",
    "CAD",
}


def validate_receipt(receipt_data: dict) -> Receipt:
    """
    Validate and clean OCR output before saving to the database.
    """

    receipt = Receipt(**receipt_data)

    # Clean merchant name
    if receipt.merchant:
        receipt.merchant = receipt.merchant.strip()

    # Standardise currency
    if receipt.currency:
        receipt.currency = receipt.currency.upper()

        if receipt.currency not in SUPPORTED_CURRENCIES:
            receipt.currency = None

    # Validate purchase date
    if receipt.purchase_date:
        try:
            parsed = datetime.strptime(receipt.purchase_date, "%Y-%m-%d")
            receipt.purchase_date = parsed.strftime("%Y-%m-%d")
        except ValueError:
            receipt.purchase_date = None

    return receipt