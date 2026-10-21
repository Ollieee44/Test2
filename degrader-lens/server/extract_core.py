"""Shared patent-extraction core for Degrader Lens.

Used by both the CLI (tools/patent_to_csv.py) and the OCSR backend (server/app.py)
so the text/SMILES/data extraction behaves identically everywhere. Mirrors the
in-browser logic in index.html.

Stages:
  - TEXT (always): identifiers, DC50/IC50/EC50/Dmax, and inline SMILES (RDKit-validated).
  - OCSR (optional): recover drawn-only structures from page images via
    decimer-segmentation + DECIMER. Heavy deps, imported lazily.
"""
from __future__ import annotations
import re

try:
    from rdkit import Chem
    from rdkit import RDLogger
    RDLogger.DisableLog("rdApp.*")
except ImportError:  # pragma: no cover
    raise SystemExit("RDKit is required: pip install rdkit")

ASSAY_COLS = ["dc50_nm", "dmax_pct", "target_ic50_nm", "ec50_nm"]


def valid_smiles(tok: str, min_heavy: int = 8):
    for cand in (tok, tok.rstrip(".,;:")):
        if not cand:
            continue
        m = Chem.MolFromSmiles(cand)
        if m is not None and m.GetNumHeavyAtoms() >= min_heavy:
            return Chem.MolToSmiles(m)
    return None


def mol_candidate(t: str) -> bool:
    return bool(
        len(t) >= 8 and re.search(r"[0-9()]", t)
        and re.fullmatch(r"[A-Za-z0-9@+\-\[\]()=#$%/\\.]+", t)
        and len(re.findall(r"[A-Z]", t)) >= 2
    )


def find_smiles(seg: str) -> str:
    lab = re.search(r"SMILES\s*[:=]\s*([^\s,;]+)", seg, re.I)
    if lab:
        c = valid_smiles(lab.group(1), 4)
        if c:
            return c
    for tok in re.split(r"[\s,;]+", seg):
        if mol_candidate(tok):
            c = valid_smiles(tok, 8)
            if c:
                return c
    return ""


def _conv(v, u):
    v = float(v)
    if not u:
        return v
    u = u.lower()
    return {"µm": v * 1e3, "um": v * 1e3, "mm": v * 1e6, "pm": v / 1e3}.get(u, v)


def extract_records(text: str) -> list[dict]:
    """Return [{id, smiles, source, data:{...}}] from patent text."""
    rows: dict[str, dict] = {}
    segs = re.split(r"(?=(?:example|compound|cpd)\s*[:#.]?\s*[0-9])", text, flags=re.I)
    for seg in segs:
        idm = re.search(r"(?:example|compound|cpd)\s*[:#.]?\s*([0-9]+[a-z]?)", seg, re.I)
        if not idm:
            continue
        label = re.sub(r"[:#.]", "", re.sub(r"\s+", " ", idm.group(0))).strip()
        cid = label[:1].upper() + label[1:]
        rec = rows.setdefault(cid, {"id": cid, "smiles": "", "source": "text", "data": {}})
        for key, pat in (("dc50_nm", r"dc\s*50"), ("target_ic50_nm", r"ic\s*50"),
                         ("ec50_nm", r"ec\s*50")):
            m = re.search(pat + r"[^0-9]{0,10}([0-9.]+)\s*(nm|µm|um|pm|mm)?", seg, re.I)
            if m and key not in rec["data"]:
                rec["data"][key] = round(_conv(m.group(1), m.group(2)), 3)
        dm = re.search(r"d\s*max[^0-9]{0,10}([0-9.]+)\s*%?", seg, re.I)
        if dm and "dmax_pct" not in rec["data"]:
            rec["data"]["dmax_pct"] = float(dm.group(1))
        if not rec["smiles"]:
            rec["smiles"] = find_smiles(seg)
    return list(rows.values())


def read_pdf_text(path: str) -> tuple[str, int]:
    try:
        from pypdf import PdfReader
    except ImportError:  # pragma: no cover
        raise SystemExit("pypdf is required: pip install pypdf")
    reader = PdfReader(path)
    return "\n".join((p.extract_text() or "") for p in reader.pages), len(reader.pages)


def run_ocsr(path: str) -> list[dict]:
    """Recover drawn structures. Returns [{id, smiles, source:'ocsr', page, data:{}}].

    Uses decimer-segmentation to crop structure depictions from each page, then
    DECIMER to predict a SMILES for each crop. Both are large ML models and are
    imported lazily so the text path never requires them.
    """
    try:
        from decimer_segmentation import segment_chemical_structures_from_file
        from DECIMER import predict_SMILES
        from PIL import Image
        import numpy as np  # noqa: F401  (decimer-segmentation returns ndarrays)
    except ImportError:
        raise RuntimeError(
            "OCSR dependencies missing. Install: "
            "pip install decimer decimer-segmentation pdf2image pillow (plus poppler)."
        )
    out: list[dict] = []
    segments = segment_chemical_structures_from_file(path)  # list of page-structure images
    for i, seg_img in enumerate(segments, 1):
        tmp = f"/tmp/_dl_seg_{i}.png"
        Image.fromarray(seg_img).save(tmp)
        try:
            smi = predict_SMILES(tmp)
            c = valid_smiles(smi, 8)
            if c:
                out.append({"id": f"OCSR-{i}", "smiles": c, "source": "ocsr",
                            "page": None, "data": {}})
        except Exception as e:  # noqa: BLE001
            out.append({"id": f"OCSR-{i}", "smiles": "", "source": "ocsr-error",
                        "page": None, "data": {}, "error": str(e)})
    return [r for r in out if r.get("smiles")]
