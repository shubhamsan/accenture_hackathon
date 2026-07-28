# ---------------------------------------------------------------------------
# Phase 2 — AI EXTRACTION — plug in your OpenAI call here
# ---------------------------------------------------------------------------
#
# import base64
# import json
# import os
#
# from openai import OpenAI
#
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
#
#
# def extract_receipt_data(image_path: str, content_type: str) -> dict:
#     # Step 1 — Read the saved file as base64
#     with open(image_path, "rb") as f:
#         image_base64 = base64.b64encode(f.read()).decode()
#
#     # Step 2 — Send to GPT-4o Vision and ask it to extract receipt fields
#     response = client.chat.completions.create(
#         model="gpt-4o",
#         messages=[{
#             "role": "user",
#             "content": [
#                 {
#                     "type": "text",
#                     "text": "Extract the following from this receipt and return as JSON: store_name, date, items (list of {name, price}), total_amount, category (e.g. groceries, dining, transport).",
#                 },
#                 {
#                     "type": "image_url",
#                     "image_url": {"url": f"data:{content_type};base64,{image_base64}"},
#                 },
#             ],
#         }],
#     )
#
#     # Step 3 — Parse and return the extracted JSON
#     return json.loads(response.choices[0].message.content)
