# ---------------------------------------------------------------------------
# Phase 5 — AI INSIGHTS — plug in your OpenAI call here
# ---------------------------------------------------------------------------
#
# import json
# import os
#
# from openai import OpenAI
#
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
#
#
# def generate_insights(receipts: list[dict]) -> str:
#     # Ask GPT to analyse spending patterns across all receipts
#     response = client.chat.completions.create(
#         model="gpt-4o",
#         messages=[
#             {
#                 "role": "system",
#                 "content": "You are a personal finance advisor. Analyse the user's spending data and provide clear, actionable insights.",
#             },
#             {
#                 "role": "user",
#                 "content": f"Here is my spending data: {json.dumps(receipts)}. Please provide: 1) a spending summary, 2) top spending categories, 3) three specific saving tips.",
#             },
#         ],
#     )
#     return response.choices[0].message.content
