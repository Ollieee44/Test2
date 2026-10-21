# Degrader Lens OCSR backend

A small FastAPI service that gives the Degrader Lens page **one-upload, fully
automatic** patent extraction — including structures that appear only as drawings,
via optical chemical-structure recognition (OCSR).

## Why a backend is needed

OCSR models (DECIMER, MolScribe) are large ML models (hundreds of MB, TensorFlow/
PyTorch). They cannot run inside a browser, and the claude.ai artifact sandbox
blocks outbound network calls, so the hosted-OCSR flow only works when you **run
the page yourself** and point it at this service. The in-browser path (text,
assay data, and inline SMILES) keeps working with no backend at all.

## Architecture

```
  Browser (Degrader Lens index.html, self-hosted)
      │  POST /extract   (multipart: pdf, ocsr=0|1)
      ▼
  FastAPI service  (server/app.py)
      ├─ read_pdf_text ──────────── pypdf            → identifiers, assay data, inline SMILES
      ├─ run_ocsr (ocsr=1) ──────── decimer-segmentation → crop each drawn structure
      │                              DECIMER             → predict SMILES per crop
      └─ validate every SMILES with RDKit
      ▼
  JSON { pages, records:[{id, smiles, source, data}], with_smiles, ocsr_used }
      │
      ▼
  Browser decomposes + plots the records (same pipeline as a pasted CSV)
```

Text/SMILES/data extraction is shared with the CLI through `extract_core.py`, so
all three entry points (in-browser, CLI, server) behave identically on the parts
they share.

## Run it

```
cd server
pip install -r requirements.txt          # core: fastapi, uvicorn, pypdf, rdkit
uvicorn app:app --host 0.0.0.0 --port 8000
```

Then open the page (served from any static server — see the main README), go to
the **Data** tab, set **OCSR server URL** to `http://localhost:8000`, tick **run
OCSR on the server**, and upload a PDF.

### Enable OCSR (drawn structures)

```
pip install decimer decimer-segmentation pdf2image pillow
# plus the system package "poppler" (e.g. apt-get install poppler-utils)
```

`GET /health` reports `ocsr_available`; the service returns a clear message if
OCSR is requested but the dependencies are missing, and falls back to text-only.

## API

- `GET /health` → `{ ok, ocsr_available }`
- `POST /extract` (multipart `pdf`, form `ocsr=0|1`) →
  `{ pages, records:[{id, smiles, source, data:{dc50_nm,…}}], with_smiles, ocsr_used, ocsr_error }`

## Accuracy & scope

- OCSR is not perfect on dense patent pages: fused/overlapping drawings,
  stereochemistry and Markush R-groups are the usual failure points. Treat
  recovered SMILES as candidates to verify, not ground truth.
- Pairing a recovered structure to the right compound number is heuristic (drawn
  structures are merged onto data-only text records in reading order). The robust
  upgrade is coordinate-based pairing: keep each structure's bounding box from
  decimer-segmentation and match it to the nearest compound label on the page.

## Production notes

- Restrict CORS: set `DL_ALLOW_ORIGINS=https://your.page.example` (defaults to `*`).
- Cap upload size with `DL_MAX_BYTES` (default 50 MB).
- OCSR is CPU-heavy; run it behind a queue/worker for large PDFs, and consider a
  GPU host. Uploaded PDFs are written to a temp file and deleted after processing.
