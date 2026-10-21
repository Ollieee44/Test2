#!/usr/bin/env python3
"""patent_to_csv.py — turn a patent PDF into a Degrader Lens CSV.

Two stages:
  1. TEXT (always on): read every page of text and pull compound identifiers,
     reported DC50 / IC50 / EC50 / Dmax values, and any machine-readable SMILES
     printed in tables or the SI. Each SMILES is validated with RDKit.
  2. OCSR (optional, --ocsr): recover structures that appear only as drawings by
     rendering pages to images and running DECIMER. These are emitted as extra
     candidate rows for you to map to compound numbers.

The output CSV (id, smiles, dc50_nm, dmax_pct, target_ic50_nm, ec50_nm) loads
directly in the Degrader Lens "Data" tab.

Install:
  pip install pypdf rdkit                      # stage 1
  pip install "decimer>=2.3" pdf2image pillow  # stage 2 (OCSR); needs poppler + a
                                               # one-time model download (~hundreds of MB)

Usage:
  python patent_to_csv.py patent.pdf -o compounds.csv
  python patent_to_csv.py patent.pdf -o compounds.csv --ocsr
"""
import argparse, csv, re, sys

try:
    from rdkit import Chem
    from rdkit import RDLogger
    RDLogger.DisableLog("rdApp.*")
except ImportError:
    sys.exit("RDKit is required: pip install rdkit")


def valid_smiles(tok, min_heavy=8):
    for cand in (tok, tok.rstrip(".,;:")):
        if not cand:
            continue
        m = Chem.MolFromSmiles(cand)
        if m is not None and m.GetNumHeavyAtoms() >= min_heavy:
            return Chem.MolToSmiles(m)
    return None


def mol_candidate(t):
    return (len(t) >= 8 and re.search(r"[0-9()]", t)
            and re.fullmatch(r"[A-Za-z0-9@+\-\[\]()=#$%/\\.]+", t)
            and len(re.findall(r"[A-Z]", t)) >= 2)


def find_smiles(seg):
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


def conv(v, u):
    v = float(v)
    if not u:
        return v
    u = u.lower()
    return {"µm": v * 1e3, "um": v * 1e3, "mm": v * 1e6, "pm": v / 1e3}.get(u, v)


def extract_records(text):
    rows = {}
    segs = re.split(r"(?=(?:example|compound|cpd)\s*[:#.]?\s*[0-9])", text, flags=re.I)
    for seg in segs:
        idm = re.search(r"(?:example|compound|cpd)\s*[:#.]?\s*([0-9]+[a-z]?)", seg, re.I)
        if not idm:
            continue
        label = re.sub(r"[:#.]", "", re.sub(r"\s+", " ", idm.group(0))).strip()
        cid = label[:1].upper() + label[1:]
        rec = rows.setdefault(cid, {"id": cid, "smiles": "", "dc50_nm": "",
                                    "dmax_pct": "", "target_ic50_nm": "", "ec50_nm": ""})
        for key, pat in (("dc50_nm", r"dc\s*50"), ("target_ic50_nm", r"ic\s*50"),
                         ("ec50_nm", r"ec\s*50")):
            m = re.search(pat + r"[^0-9]{0,10}([0-9.]+)\s*(nm|µm|um|pm|mm)?", seg, re.I)
            if m and rec[key] == "":
                rec[key] = round(conv(m.group(1), m.group(2)), 3)
        dm = re.search(r"d\s*max[^0-9]{0,10}([0-9.]+)\s*%?", seg, re.I)
        if dm and rec["dmax_pct"] == "":
            rec["dmax_pct"] = float(dm.group(1))
        if not rec["smiles"]:
            rec["smiles"] = find_smiles(seg)
    return list(rows.values())


def read_pdf_text(path):
    try:
        from pypdf import PdfReader
    except ImportError:
        sys.exit("pypdf is required for text extraction: pip install pypdf")
    reader = PdfReader(path)
    return "\n".join((p.extract_text() or "") for p in reader.pages), len(reader.pages)


def run_ocsr(path):
    """Best-effort: render pages and recover drawn structures with DECIMER."""
    try:
        from DECIMER import predict_SMILES
        from pdf2image import convert_from_path
    except ImportError:
        print("  [ocsr] skipped — install: pip install decimer pdf2image pillow (+poppler)",
              file=sys.stderr)
        return []
    out = []
    for i, img in enumerate(convert_from_path(path, dpi=300), 1):
        tmp = f"/tmp/_page_{i}.png"
        img.save(tmp)
        try:
            smi = predict_SMILES(tmp)
            c = valid_smiles(smi, 8)
            if c:
                out.append({"id": f"OCSR-p{i}", "smiles": c, "dc50_nm": "",
                            "dmax_pct": "", "target_ic50_nm": "", "ec50_nm": ""})
        except Exception as e:  # noqa: BLE001
            print(f"  [ocsr] page {i}: {e}", file=sys.stderr)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("-o", "--out", default="compounds.csv")
    ap.add_argument("--ocsr", action="store_true",
                    help="also recover drawn structures with DECIMER (heavy deps)")
    args = ap.parse_args()

    text, npages = read_pdf_text(args.pdf)
    rows = extract_records(text)
    n_struct = sum(1 for r in rows if r["smiles"])
    print(f"text: {npages} pages -> {len(rows)} records, {n_struct} with a SMILES",
          file=sys.stderr)

    if args.ocsr:
        ocsr = run_ocsr(args.pdf)
        print(f"ocsr: recovered {len(ocsr)} structure(s)", file=sys.stderr)
        rows += ocsr

    cols = ["id", "smiles", "dc50_nm", "dmax_pct", "target_ic50_nm", "ec50_nm"]
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows -> {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
