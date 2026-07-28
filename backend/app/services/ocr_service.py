import base64
import json
from pathlib import Path

from app.services.receipt_verification import get_openai_client

RECEIPT_EXTRACTION_PROMPT = """
You are an expert receipt extraction assistant.

Extract the receipt into VALID JSON only.

Return exactly this schema:

{
  "merchant": "",
  "purchase_date": "",
  "currency": "",
  "subtotal": 0,
  "tax": 0,
  "total": 0,
  "payment_method": "",
  "items": [
    {
      "name": "",
      "quantity": 1,
      "unit_price": 0,
      "total_price": 0,
      "category": ""
    }
  ]
}

Rules:

- Return ONLY JSON.
- Never explain anything.
- Use null if information is missing.
- Dates should be in YYYY-MM-DD format whenever possible.
- Currency should use ISO codes (GBP, USD, EUR, INR, etc.).
- Do not invent missing values.
- Preserve item names exactly as shown on the receipt.
"""


def _encode_image(image_path: Path) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def extract_receipt_data(image_path: Path) -> dict | None:
    """
    Extract structured receipt data (merchant, items, totals) from a saved
    receipt image using GPT-4.1. Returns None if extraction or parsing fails.
    """

    client = get_openai_client()
    base64_image = _encode_image(image_path)

    response = client.responses.create(
        model="gpt-4.1",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": RECEIPT_EXTRACTION_PROMPT},
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{base64_image}",
                    },
                ],
            }
        ],
    )

    output_text = response.output_text.strip()

    if output_text.startswith("```"):
        output_text = output_text.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(output_text)
    except json.JSONDecodeError:
        return None
