import json
import os
from pathlib import Path

import cv2
from openai import OpenAI


def get_openai_client():
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def crop_to_bounding_box(
    image_path: Path,
    bounding_box: dict,
    padding_frac: float = 0.03,
) -> bool:
    """
    Crop the image to the detected receipt bounding box.
    Returns True if cropping succeeds, otherwise False.
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
        return False

    height, width = image.shape[:2]

    pad_x = (x_max - x_min) * padding_frac
    pad_y = (y_max - y_min) * padding_frac

    left = max(0, int((x_min - pad_x) * width))
    top = max(0, int((y_min - pad_y) * height))
    right = min(width, int((x_max + pad_x) * width))
    bottom = min(height, int((y_max + pad_y) * height))

    if right - left < 10 or bottom - top < 10:
        return False

    cropped = image[top:bottom, left:right]
    cv2.imwrite(str(image_path), cropped)

    return True


def _parse_json_response(raw_content: str) -> dict:
    """
    Remove markdown code fences (if present) and parse JSON.
    """

    raw_content = raw_content.strip()

    if raw_content.startswith("```"):
        raw_content = raw_content.strip("`")

        if raw_content.startswith("json"):
            raw_content = raw_content[4:]

        raw_content = raw_content.strip()

    return json.loads(raw_content)


def verify_is_receipt(image_base64: str, content_type: str) -> dict:
    """
    Verify whether the uploaded image is a receipt and return
    the receipt bounding box if detected.
    """

    client = get_openai_client()

    response = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Look at this image and determine whether it shows a "
                            "physical or digital receipt (proof of purchase with "
                            "items, prices, and/or a total). Respond with strict "
                            "JSON only, in this exact shape:\n"
                            '{"is_receipt": true or false, '
                            '"reason": "short reason if not a receipt, else empty string", '
                            '"bounding_box": {"x_min": 0-1, "y_min": 0-1, "x_max": 0-1, "y_max": 0-1} '
                            "or null if no receipt is detected}\n"
                            "Bounding box coordinates are fractions of the image "
                            "width/height, measured from the top-left corner."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{content_type};base64,{image_base64}"},
                    },
                ],
            }
        ],
        max_tokens=200,
    )

    return _parse_json_response(response.choices[0].message.content)

