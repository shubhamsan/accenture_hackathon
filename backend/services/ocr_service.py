import os
import base64
import json

from dotenv import load_dotenv
from openai import OpenAI

from prompts.receipt_prompt import RECEIPT_EXTRACTION_PROMPT

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def encode_image(image_path: str) -> str:
    """Convert image to Base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def extract_receipt(image_path: str):
    """
    Extract structured receipt data from an image.
    """

    base64_image = encode_image(image_path)

    response = client.responses.create(
        model="gpt-4.1",
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": RECEIPT_EXTRACTION_PROMPT,
                    },
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{base64_image}",
                    },
                ],
            }
        ],
    )

    output_text = response.output_text.strip()

    # Remove Markdown code fences if present
    if output_text.startswith("```"):
        output_text = output_text.replace("```json", "")
        output_text = output_text.replace("```", "")
        output_text = output_text.strip()

    try:
        return json.loads(output_text)

    except json.JSONDecodeError as e:
        print("❌ Failed to parse JSON")
        print(e)
        print(output_text)
        return None