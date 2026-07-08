import json
import re

import requests
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.2"


class ExtractRequest(BaseModel):
    text: str


class ExtractResponse(BaseModel):
    vendor: str
    amount: float
    currency: str
    date: str


PROMPT = """
Extract these invoice fields.

Return ONLY valid JSON.

Schema:
{
  "vendor": string,
  "amount": number,
  "currency": "USD|EUR|GBP",
  "date": "YYYY-MM-DD"
}

Rules:
- vendor = company/vendor name
- amount = total amount due
- currency = exactly USD, EUR or GBP
- date = payment due date in YYYY-MM-DD format

Do not explain.
Do not use markdown.
"""


@app.post("/extract", response_model=ExtractResponse)
def extract(req: ExtractRequest):

    if not req.text.strip():
        return ExtractResponse(
            vendor="",
            amount=0,
            currency="",
            date=""
        )

    try:
        r = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": PROMPT,
                    },
                    {
                        "role": "user",
                        "content": req.text,
                    },
                ],
                "stream": False,
            },
            timeout=60,
        )

        response = r.json()

        content = response["message"]["content"].strip()

        # remove ```json ... ```
        content = re.sub(r"^```json", "", content, flags=re.I).strip()
        content = re.sub(r"^```", "", content).strip()
        content = re.sub(r"```$", "", content).strip()

        data = json.loads(content)

        return ExtractResponse(
            vendor=str(data.get("vendor", "")),
            amount=float(data.get("amount", 0)),
            currency=str(data.get("currency", "")).upper(),
            date=str(data.get("date", "")),
        )

    except Exception:
        # Never return HTTP 500
        return ExtractResponse(
            vendor="",
            amount=0,
            currency="",
            date=""
        )
