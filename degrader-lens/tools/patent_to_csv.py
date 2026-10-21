#!/usr/bin/env python3
"""patent_to_csv.py — turn a patent PDF into a Degrader Lens CSV.

Stage 1 (TEXT, always on): read every page of text and pull compound identifiers,
reported DC50 / IC50 / EC50 / Dmax values, and any machine-readable SMILES printed
in tables or the SI. Each SMILES is validated with RDKit.

Stage 2 (OCSR, --ocsr): recover structures that appear only as drawings by
segmenting page images and running DECIMER.

Extraction logic is shared with the backend in ../server/extract_core.py.

Install:
  pip install pypdf rdkit                                   # stage 1
  pip install decimer decimer-segmentation pdf2image pillow # stage 2 (+poppler); large model download

Usage:
  python patent_to_csv.py patent.pdf -o compounds.csv [--ocsr]
"""
import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "server"))
import extract_core as core  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("-o", "--out", default="compounds.csv")
    ap.add_argument("--ocsr", action="store_true",
                    help="also recover drawn structures with DECIMER (heavy deps)")
    args = ap.parse_args()

    text, npages = core.read_pdf_text(args.pdf)
    records = core.extract_records(text)
    n_struct = sum(1 for r in records if r["smiles"])
    print(f"text: {npages} pages -> {len(records)} records, {n_struct} with a SMILES",
          file=sys.stderr)

    if args.ocsr:
        try:
            recovered = core.run_ocsr(args.pdf)
            data_only = [r for r in records if not r["smiles"]]
            for rec, got in zip(data_only, recovered):
                rec["smiles"] = got["smiles"]
            records += recovered[len(data_only):]
            print(f"ocsr: recovered {len(recovered)} structure(s)", file=sys.stderr)
        except RuntimeError as e:
            print(f"ocsr: {e}", file=sys.stderr)

    cols = ["id", "smiles"] + core.ASSAY_COLS
    with open(args.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in records:
            w.writerow([r["id"], r["smiles"]] + [r["data"].get(c, "") for c in core.ASSAY_COLS])
    print(f"wrote {len(records)} rows -> {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
