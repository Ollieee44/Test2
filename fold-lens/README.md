# Fold Lens

A single-page molecular viewer for experimental structures and structure predictions, driven by plain-language commands.

- **Load**: PDB, mmCIF, BinaryCIF, SDF, MOL2, XYZ, PQR, gzipped files, or whole zips (AlphaFold Server downloads). Fetch by PDB ID or UniProt accession when opened in a normal browser tab (the claude.ai artifact sandbox blocks outside requests).
- **Predictions**: pLDDT from the B-factor column; PAE, pTM, ipTM, chain-pair ipTM and ranking scores from AlphaFold DB, AlphaFold 3 / Server, ColabFold, Boltz-1/2 (JSON + NPZ) and Chai-1 (NPZ) output files. Files are matched to their model by name and token count.
- **Commands**: "show the binding site of ATP and label it", "color by pae relative to chain B", "align model 2 onto model 1", "hide very low confidence", "show contacts between chain A and chain C", "delete waters", "export pdb". Unrecognised requests go to Claude when the page runs as a claude.ai artifact.
- **Co-fold builder**: turns the loaded entities (plus pasted sequences, CCD codes or SMILES) into inputs for AlphaFold 3, AlphaFold Server, Boltz, Chai-1, Protenix and ColabFold.

Open `index.html` through any static web server (e.g. `python3 -m http.server`) so the bundled samples in `samples/` load. Samples are PDB entries 4CUP, 7DDO and 1LCD (public domain, from the Biopython test suite).

Rendering uses [3Dmol.js](https://3dmol.csb.pitt.edu) 2.5.3; zip/NPZ reading uses fflate 0.8.2.
