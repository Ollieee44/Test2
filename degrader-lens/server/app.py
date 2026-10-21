"""Degrader Lens OCSR backend.

A small FastAPI service that takes a patent PDF and returns extracted records
(identifiers, assay data, inline SMILES) plus — when requested and available —
structures recovered from drawings via OCSR. The Degrader Lens page POSTs the PDF
here when you set an "OCSR server URL" in its Data tab.

This is only reachable when you self-host the page (same origin, or this server
with CORS). The claude.ai artifact sandbox blocks outbound network calls, so the
in-browser extraction there stays text/SMILES only.

Run:
  pip install -r requirements.txt
  uvicorn app:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations
import os
import tempfile

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import extract_core as core

app = FastAPI(title="Degrader Lens OCSR backend", version="1.0")

# Dev-friendly CORS. In production, restrict allow_origins to your deployed page.
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("DL_ALLOW_ORIGINS", "*").split(","),
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

MAX_BYTES = int(os.environ.get("DL_MAX_BYTES", 50 * 1024 * 1024))  # 50 MB default


@app.get("/health")
def health():
    ocsr = True
    try:
        import decimer_segmentation  # noqa: F401
        import DECIMER  # noqa: F401
    except ImportError:
        ocsr = False
    return {"ok": True, "ocsr_available": ocsr}


@app.post("/extract")
async def extract(pdf: UploadFile = File(...), ocsr: str = Form("0")):
    if (pdf.content_type or "") not in ("application/pdf", "application/octet-stream") \
            and not (pdf.filename or "").lower().endswith(".pdf"):
        raise HTTPException(400, "Upload a PDF file.")
    data = await pdf.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(413, f"PDF exceeds {MAX_BYTES} bytes.")

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
        tf.write(data)
        path = tf.name
    try:
        text, pages = core.read_pdf_text(path)
        records = core.extract_records(text)
        ocsr_used, ocsr_error = False, None
        if ocsr in ("1", "true", "True", "on"):
            try:
                recovered = core.run_ocsr(path)
                # merge: fill structures onto data-only text records in order, keep extras
                data_only = [r for r in records if not r["smiles"]]
                for rec, got in zip(data_only, recovered):
                    rec["smiles"] = got["smiles"]
                    rec["source"] = "text+ocsr"
                for extra in recovered[len(data_only):]:
                    records.append(extra)
                ocsr_used = True
            except RuntimeError as e:
                ocsr_error = str(e)
        return {
            "pages": pages,
            "records": records,
            "with_smiles": sum(1 for r in records if r["smiles"]),
            "ocsr_used": ocsr_used,
            "ocsr_error": ocsr_error,
            "filename": pdf.filename,
        }
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass
