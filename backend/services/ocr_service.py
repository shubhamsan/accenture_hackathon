import os
import base64
import json

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_receipt(image_path: str):
    """
    Sends a receipt image to OpenAI and returns structured JSON.
    """

    # Read image
    with open(image_path, "rb") as image_file:
        image_bytes = image_file.read()

    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    response = client.responses.create(
        model="gpt-4.1",
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": """
You are an OCR assistant.

Extract the receipt into JSON.

Return ONLY valid JSON.

{
  "merchant": "",
  "purchase_date": "",
  "currency": "",
  "subtotal": 0,
  "tax": 0,
  "total": 0,
  "items": [
    {
      "name": "",
      "quantity": 1,
      "price": 0
    }
  ]
}
"""
                    },
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{image_base64}"
                    }
                ]
            }
        ]
    )

    return json.loads(response.output_text)