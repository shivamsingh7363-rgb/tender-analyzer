import os
import base64
import json
import httpx
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List

app = FastAPI(title="Tender Analyzer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

SYSTEM_PROMPT = """You are an expert tender analysis AI for a consulting firm. Your job is to carefully read tender documents (government/corporate procurement tenders) and evaluate them against a client's checklist.

For each checklist item, determine:
- MET: The tender clearly satisfies this requirement with specific details provided
- PARTIAL: Some information is present but incomplete or ambiguous  
- NOT MET: The requirement is not addressed or clearly cannot be fulfilled

Respond ONLY with valid JSON. No markdown, no preamble, no explanation outside the JSON.

JSON structure:
{
  "tender_title": "string - extracted tender title or project name",
  "tender_reference": "string - tender number/reference if found",
  "issuing_authority": "string - organization issuing the tender",
  "overall_verdict": "string - 2-3 sentence executive summary for the client",
  "overall_score": number between 0 and 100,
  "results": [
    {
      "item": "string - the checklist item",
      "status": "MET" or "PARTIAL" or "NOT MET",
      "detail": "string - specific explanation of finding, 1-2 sentences",
      "evidence": "string - brief reference or paraphrased finding from document, or empty string"
    }
  ]
}"""


@app.get("/", response_class=HTMLResponse)
async def root():
    return FileResponse("static/index.html")


@app.post("/analyze")
async def analyze_tender(
    pdf: UploadFile = File(...),
    checklist: str = Form(...)
):
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured on server.")

    if not pdf.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    pdf_bytes = await pdf.read()
    if len(pdf_bytes) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="PDF too large. Please upload a file under 20MB.")

    pdf_base64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")

    try:
        checklist_items = json.loads(checklist)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid checklist format.")

    if not checklist_items:
        raise HTTPException(status_code=400, detail="Checklist is empty.")

    checklist_str = "\n".join(f"{i+1}. {item}" for i, item in enumerate(checklist_items))

    user_prompt = f"""Here is the tender document as a PDF. Please analyze it against the following checklist:

CHECKLIST:
{checklist_str}

Analyze every item carefully against the document. Return only valid JSON."""

    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 4000,
        "system": SYSTEM_PROMPT,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": user_prompt
                    }
                ]
            }
        ]
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            ANTHROPIC_URL,
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json=payload
        )

    if response.status_code != 200:
        error_detail = response.json().get("error", {}).get("message", "Anthropic API error")
        raise HTTPException(status_code=502, detail=f"AI API error: {error_detail}")

    data = response.json()
    raw_text = "".join(block.get("text", "") for block in data.get("content", []))
    clean_text = raw_text.replace("```json", "").replace("```", "").strip()

    try:
        result = json.loads(clean_text)
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to parse AI response. Please try again.")

    return result


@app.get("/health")
async def health():
    return {"status": "ok", "api_key_set": bool(ANTHROPIC_API_KEY)}
