# Degrader Lens

A single-page workbench for **targeted protein degraders** — heterobifunctional
degraders (PROTACs) and molecular glue degraders. It turns a set of structures
plus their reported biological data into an interactive view of the chemistry and
the structure–activity relationships.

Everything runs in the browser. Structures are parsed, depicted and analysed with
[RDKit](https://www.rdkit.org/) compiled to WebAssembly; nothing is uploaded.

## What it does

- **Degrader decomposition.** Every molecule is split into **warhead / target
  ligand · linker · E3 ligand** and the three regions are colour-coded on the 2D
  depiction. The **E3-ligase ligand is detected automatically** from a curated
  substructure library (CRBN glutarimide, VHL hydroxyprolinamide, MDM2 nutlin,
  DCAF15 arylsulfonamide). Give a shared **warhead SMARTS** and the linker is
  resolved exactly as the acyclic chain between the two anchors; without one, the
  E3 ligand is still highlighted.
- **Interactive visualisation.** A gallery of region-highlighted structures with
  text/SMARTS filtering, a detail view with a large depiction, an arbitrary SMARTS
  highlight box, calculated properties (with beyond-Rule-of-5 flags appropriate to
  this chemotype) and the compound's biological data.
- **SAR landscape.** Plot any measured or computed property against any other —
  linker length vs DC₅₀, MW vs Dmax, cLogP vs IC₅₀, and so on — with a log axis
  for potency, colour by E3 ligase or series, per-series trend lines, hover
  details and a correlation read-out that recognises the biphasic nature of
  linker-length SAR (an optimum, not a slope).
- **Data table.** Sortable, with DC₅₀ shaded by potency; copy the whole set as CSV
  or SMILES.
- **Upload a patent PDF.** The app reads every page of text (via PDF.js) and pulls
  compound identifiers, reported IC₅₀ / DC₅₀ / EC₅₀ / Dmax values, and any
  machine-readable **SMILES** printed in tables or the SI — each validated with
  RDKit. Compounds with a SMILES are decomposed and plotted immediately; the rest
  are kept as data-only rows to attach a structure to later.
- **Other ingestion.** Load the bundled sample set, paste or upload **CSV**
  (`id, smiles, dc50_nm, dmax_pct, …`), a **SMILES list**, or an **SDF**; set the
  warhead scaffold; or paste a patent text excerpt.

## Versions

- **`index-v5.html`** — v4 plus three refinements. **Linker length is the chain**
  between the warhead and the E3 (the backbone atoms on the path between them),
  reported separately from the linker colour region (which stays "everything that
  isn't the warhead or E3"). **Push-to-all is stronger**: define the warhead and/or
  E3 on one compound and it splits the whole series — the E3 is matched by your
  captured fragment *or* the built-in E3-ligase anchor library, so defining just the
  warhead is enough to decompose a congeneric set, and it reports how many matched.
  **Compound numbering is unified**: "Compound 9", "Example 9" and a bare "9" in a
  data table all count as the same compound, so a scanned table row merges onto its
  structure by number.
- **`index.html`** — the original: opens with a loaded sample dataset.
- **`index-v4.html`** — v3 plus an **interactive structure view** and a **fast,
  decoupled PDF flow**. The depiction is clean (standard element colours; region
  highlighting off by default) and you define the regions directly on the drawing:
  **drag a lasso** around part of the structure (or click individual atoms) to
  select it — the **fragment SMILES** is read out and copyable — then press one of
  three obvious buttons (**Warhead / target (POI)**, **E3 ligand**, **Linker**).
  Define the **warhead and E3 on one example** and **“apply to all compounds”**
  pushes the same fragments onto every structure in the series and **infers each
  linker as the chain in between** — set it once, done for the whole set. (You can
  also pick the two linker ends and it splits the rest.) On a PDF, the **biology SAR
  comes out in seconds from the text alone**
  (compound numbers + assay data + any inline SMILES, all plotted — even for
  compounds with no structure); reading **drawn** structures with Claude is a
  separate, optional background step with a **Fast / Balanced / Best** speed control,
  an ETA and a Stop button, so it never blocks the SAR. The **assay fields are not
  pre-defined** — the table columns and SAR axes are built from whatever the
  document contains, including **qualitative / bucketed potency** (+, ++, +++, letter
  grades, % inhibition), which the SAR can plot as a categorical axis.
- **`index-v3.html`** — v2 plus: **automatic scaffold-free decomposition** (warhead/
  linker/E3 split and linker length populate for any PROTAC, no scaffold needed),
  **target (POI) detection** from the document text, **tidy-up** that keeps only
  numbered final compounds (drops intermediates/building blocks), and **OCSR
  accuracy checks** — each Claude-read structure returns a molecular formula and a
  confidence; a formula mismatch or low confidence flags it "needs review" (with a
  filter and badges), and a per-compound "re-check with Claude" re-verifies it
  against the drawing.
- **`index-v2.html`** — a blank landing built around dropping in a document. No
  preloaded data; works on **patents and papers**; accepts **CSV / Excel (.xlsx) /
  SDF / SMILES**; and on a PDF it does a **two-pass focused scan** — a quick text
  pass locates the pages holding the numbered compound structures (usually the
  tables toward the end), then Claude reads only those, skipping the rest (with an
  optional page-range limit). Both share the same chemistry engine and the three
  OCSR routes below.

## Running it

Open `index.html` through any static web server so the WebAssembly module in
`RDKit_minimal.wasm` loads next to it:

```
python3 -m http.server
# then open http://localhost:8000/index.html
```

Opening the file directly with `file://` will not load the WASM module. Chemical
names can be resolved to SMILES via OPSIN or PubChem when the page is opened in a
normal browser tab.

## How the chemistry works

- **E3 detection** — each compound is matched against the anchor SMARTS in
  `E3_ANCHORS`; the first hit assigns the ligase and the atoms of the E3 ligand.
- **Warhead** — matched from a user-supplied common scaffold SMARTS (R-group /
  common-core style), which is the accurate route for region-based SAR across a
  congeneric series.
- **Linker** — the acyclic atoms on the shortest bond path between the E3 anchor
  and the warhead match. The molecular graph (atoms, bonds and ring membership via
  bridge detection) is read from the RDKit mol block. Linker length and ether-oxygen
  (PEG-like) count feed the SAR axes.
- **Properties** — RDKit descriptors: MW, cLogP, TPSA, HBD/HBA, rotatable bonds,
  rings, Fsp³, heavy-atom count.

The anchor library and the decomposition/linker logic were validated against
reference ligands (thalidomide, lenalidomide, pomalidomide, VH032, nutlin,
indisulam) before being used here.

## The sample dataset

The bundled set is **illustrative**: a congeneric warhead linked through PEG
linkers of increasing length to either a pomalidomide (CRBN) or a VH032 (VHL)
recruiter, plus three monovalent glues. The structures are chemically valid and
the reported numbers follow the characteristic bell-shaped linker–degradation
relationship, but they are synthetic demonstration data, not measurements of any
specific disclosed compound. Replace them with your own via the **Data** tab.

## Patent PDFs: what is and isn't automatic

Uploading a PDF gets you everything that is in the document as **text**:
identifiers, assay values, and machine-readable SMILES (common in modern patent
tables and SI). For those compounds you get structures + SAR straight from the PDF.

A structure that appears **only as a drawing** (an image) needs optical
chemical-structure recognition. There are three routes, in order of least setup:

**1. Claude vision, in the browser (no install) — one upload for everything.** In
the published claude.ai artifact, tick **“read drawn structures too”** next to
*Upload patent PDF*. The tool then reads the text (identifiers + assay data +
inline SMILES), finds the pages that contain structure drawings, has Claude read
each drawing into a SMILES on your own account, validates it with RDKit, and
**merges every structure onto its compound by example number** — so one upload
gives you structures and data together. Structures Claude read are tagged
“Claude-read” so you can check them against the drawings (it's a strong assist,
not guaranteed correct on complex degraders). The *Read drawn structures with
Claude* panel also lets you read a single snipped image or one rendered page by
hand. This runs only in the claude.ai artifact, where the page can call Claude.

**2. The local companion (install, most accurate on batches).** For image-only
patents processed in bulk, run the bundled companion:

```
pip install pypdf rdkit                       # text + data + inline SMILES
python tools/patent_to_csv.py patent.pdf -o compounds.csv

pip install "decimer>=2.3" pdf2image pillow   # add OCSR for drawn structures
python tools/patent_to_csv.py patent.pdf -o compounds.csv --ocsr
```

It writes a CSV in this tool's format; load it in the **Data** tab.

**3. A self-hosted backend (one upload, fully automatic).** Run the OCSR backend
in `server/` (see `server/README.md`) and set its URL in the Data tab; uploads are
then processed server-side, drawings included. This needs you to host the page
yourself — the claude.ai artifact sandbox blocks outbound calls.

Routes 2 and 3 use DECIMER; route 1 uses Claude's own vision.

The tool is deliberately honest about this boundary rather than guessing
structures from pictures.

## Other limitations
- Fully automatic warhead/linker splitting of an arbitrary molecule is a hard
  problem; region-based SAR is accurate when a shared warhead scaffold is supplied.
- Descriptors are 2D/topological estimates (cLogP is Crippen), not measured values.

Structure handling uses [RDKit.js](https://github.com/rdkit/rdkit-js) 2025.3.4
(RDKit 2025.03); PDF reading uses [PDF.js](https://mozilla.github.io/pdf.js/)
3.11.174. Both are bundled as same-origin files (`RDKit_minimal.wasm`,
`pdf.min.js`, `pdf.worker.min.js`), so the page works offline once loaded.
