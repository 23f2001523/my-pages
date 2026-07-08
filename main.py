import re
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class ExtractRequest(BaseModel):
    text: str


class ExtractResponse(BaseModel):
    vendor: str
    amount: float
    currency: str
    date: str


@app.post("/extract", response_model=ExtractResponse)
def extract(req: ExtractRequest):

    text = req.text.strip()

    if not text:
        return ExtractResponse(
            vendor="",
            amount=0,
            currency="",
            date=""
        )

    # Date
    date_match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", text)
    date = date_match.group(1) if date_match else ""

    # Currency
    currency_match = re.search(r"\b(USD|EUR|GBP)\b", text, re.I)
    currency = currency_match.group(1).upper() if currency_match else ""

    # Amount
    amount = 0.0

    patterns = [
        r"Total\s+Due[: ]*\$?([0-9]+(?:\.[0-9]+)?)",
        r"Amount\s+Due[: ]*\$?([0-9]+(?:\.[0-9]+)?)",
        r"Total[: ]*\$?([0-9]+(?:\.[0-9]+)?)",
        r"\$([0-9]+(?:\.[0-9]+)?)",
        r"([0-9]+(?:\.[0-9]+)?)\s*(USD|EUR|GBP)"
    ]

    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            amount = float(m.group(1))
            break

    # Vendor
    vendor = ""

    vendor_patterns = [
        r"Vendor[: ]*(.+)",
        r"From[: ]*(.+)",
        r"Supplier[: ]*(.+)",
        r"Bill From[: ]*(.+)"
    ]

    for p in vendor_patterns:
        m = re.search(p, text, re.I)
        if m:
            vendor = m.group(1).split("\n")[0].strip()
            break

    # Fallback:
    # first non-empty line that isn't obviously another field
    if not vendor:
        for line in text.splitlines():
            line = line.strip()
            if (
                line
                and not re.match(
                    r"(invoice|date|due|total|amount|currency)",
                    line,
                    re.I,
                )
            ):
                vendor = line
                break

    return ExtractResponse(
        vendor=vendor,
        amount=amount,
        currency=currency,
        date=date,
    )
