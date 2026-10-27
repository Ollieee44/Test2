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

- **`index-v12.html`** — v11 plus a **PowerPoint "structures + data" scan deck** built straight from a
  patent PDF. Tick *"also spit out a PowerPoint of structures + data"* (or press **Build deck now**) and
  it screenshots the relevant pages into a `.pptx` — one page per slide, each captioned with the
  compound numbers and any DC₅₀/Dmax — for a quick side-by-side scan. It targets the pages that show
  **example structures whose compounds have biological data**, plus the **results-table** pages:
  candidates are picked fast from the text pass (a page is a candidate if it's a results table with
  several assay values, or carries drawings and names a data-bearing compound), and when Claude is
  available it **sense-checks each candidate page image** so synthesis schemes are dropped, structure
  pages are kept only when their compounds have activity, and a data table with no drawings is still
  caught. **Every slide carries the biological data alongside the structures** — a compact table of the
  compounds on that page (DC₅₀, Dmax, other assays, linker length), pulled from the already-extracted
  data so a chemist can go compound-by-compound — and the deck opens with a **summary slide** of the
  whole set. Slides preserve each page's aspect ratio (no squishing). The Claude sense-check runs its
  pages **in parallel** (much faster than one-by-one). Honours the page-range box, caps the deck for
  speed, and saves through the downloads capability (PptxGenJS). The optional, slower Claude
  structure-reading (into live SMILES) remains the separate path.
- **`index-v11.html`** — v10 plus **exports, a scan sheet, QC validation, and patent-by-ID input.**
  **Exports** (Data table): **Excel (.xlsx)**, **SDF** (molfiles + SD tags — the native format for
  DataWarrior / Vortex), and CSV, each carrying the curated SMILES, region method, linker length,
  total length, stereocentres, calculated properties, QC status and all assay data — with a
  per-compound **"structure confirmed"** flag and an *export-only-confirmed* option. A **scan sheet**
  builds a montage of every compound that has both a structure and biological data (structure · id ·
  DC₅₀/Dmax/linker) for a side-by-side eyeball scan, downloadable as **PNG or SVG**. **QC validation**
  parses reported characterisation — molecular **formula, MW, HRMS/ESI m/z [M+H]⁺, HPLC purity** —
  from the text/tables (and from Claude-read pages) and checks it against the values computed from the
  SMILES: a match marks the structure **QC-consistent** (and can auto-confirm it), a mismatch flags it
  for review (a composition check — isomers share a mass/formula, so it supports rather than proves
  the connectivity). And you can paste a **patent URL or ID** (e.g. `WO2025/072629A1`): a self-hosted
  copy fetches and parses it directly; the sandboxed claude.ai artifact (no outbound network) instead
  turns the ID into a one-click Google Patents link to grab the PDF. An **Ask tab** answers free-text
  questions about the loaded set — *"which compound has the best DC₅₀/Dmax balance?"*, *"summarise the
  linker-length SAR"*, *"which analogs differ only in the E3?"* — by passing the **data table plus
  each compound's SMILES** (regions, linker/total length, potency, Dmax, stereo, QC) to Claude as the
  sole context, so answers are about *your* compounds, not the wider literature. (Runs only where the
  page can call Claude — the published artifact.) The RDKit WASM and PDF.js are now **published as
  companion files** next to the page so the engine and PDF reading work in the published artifact, not
  only on a self-hosted copy.
- **`index-v10.html`** — v9 plus a **sharper auto-split** and **learning that auto-completes the
  decomposition from your own edits**. The automatic warhead/linker/E3 split no longer traces to the
  *farthest* ring (which swallowed a POI's own internal ethers/amides and called them linker); it
  now takes the E3 ligand's ring system as one end, the largest ring-bearing fragment beyond it as
  the warhead, and the **linker is only the acyclic chain up to the warhead's first ring** — so a
  multi-ring POI keeps its internal connectors. On top of that, **every compound you decompose by
  hand becomes a labelled example**. Its E3 and warhead fragments go into a match library and its
  full atom→region map is kept, so once you have **three hand-labelled compounds the tool
  auto-completes the rest**: a congener is split by fragment match, and a not-quite-identical analog
  is labelled by **MCS atom-mapping transfer** from the most similar example you labelled. Your own
  labels are never overwritten; auto-completed ones are badged **"learned"** (vs **"manual"**) with a
  one-click *Looks right ✓* to confirm (or just re-assign to correct — which teaches it). The library
  **persists in your browser and keeps improving across uploads**, with a status bar showing how many
  examples it holds and how many it filled in, plus an on/off toggle and a clear button. This is
  instance-based learning (no server, no trained model) — but for a congeneric series it means
  labelling a handful and getting the whole set.
- **`index-v9.html`** — v8 plus a **structure editor** and **Dmax throughout the interpretation**.
  Each compound now has an **Edit structure** panel: edit the **SMILES directly**, or describe the
  change in **plain language** ("add a fluorine to the warhead ring", "make the linker a 4-carbon
  chain", "invert the hydroxyproline stereocentre", "swap the CRBN recruiter for VHL") and Claude
  turns it into an edited SMILES, which is **validated with RDKit and shown as a before/after preview
  with the change highlighted** before you apply it — with a one-click **revert**. The **Interpret
  tab now reports both degrader read-outs**, not just potency: matched pairs show the **DC₅₀
  fold-change and the Dmax change** side by side; **linker-length SAR** reports the potency optimum
  **and** where Dmax peaks (they are often different linker lengths); "what tracks with…" shows two
  correlation panels — **potency (DC₅₀)** and **efficacy (Dmax)**; and the compare tool spells out
  both. Pairs can now be formed on Dmax alone when no shared potency assay is present.
- **`index-v8.html`** — v7 plus **assigned stereochemistry** and **comparative examples**.
  Every structure's **CIP configuration is extracted** (RDKit `get_stereo_tags`): the Compound panel
  lists each stereocentre's R/S, counts **defined vs unspecified** centres (Table columns too), and
  flags any centre left unspecified — a degrader's recruiter and warhead are configuration-specific,
  so an unassigned centre means the active isomer isn't pinned down. A **recruiter-configuration
  check** warns when an E3 ligand's key stereocentres are unspecified (the VHL hydroxyproline must be
  the trans (2S,4R) isomer to bind). The **comparison engine is now stereo-aware**: after the MCS
  atom mapping, mapped stereocentres whose R/S is inverted (or double bonds whose E/Z flips) are
  reported as a difference, so an **epimer/diastereomer pair** — identical skeleton, zero unmapped
  atoms — is caught and shows up in matched-molecular-pairs as a *stereochemistry* change with its
  fold-change. Structures **read from a drawing by Claude are flagged to verify stereochemistry**
  (wedge/hash perception is the least reliable part of OCSR). Finally, **comparative / reference /
  control examples are pulled out of patent tables and the text**, standardised to **"Comparative
  Example N"**, kept as a distinct namespace (so a comparative never merges with the same-numbered
  example), badged in the gallery, and **included in the interpretation** — a comparative vs its
  parent example is exactly the matched pair that quantifies why a change matters (the demo loader's
  binding-dead *Comparative Example 1* pairs with *Compound 3* for a ~560× loss).
- **`index-v7.html`** — v6 plus sharper decomposition, an SAR-interpretation tab, and a
  self-checking reader. The **linker is now strictly the contiguous chain between E3 and
  POI**: both ligands are flood-filled outward, so a ring, substituent or stray oxygen that
  the match/lasso didn't cover is pulled back into its ligand instead of being coloured as
  linker (a fuller VHL recruiter anchor is included too). **Two true length metrics** replace
  the old atom headcount: **linker length** is the through-bond span between the linker region's
  two extremes (so a ring in the linker counts as its path length, not every ring atom), and
  **total length** is the fully-extended reach from the POI (warhead) end to the E3 end — the
  max warhead-to-E3 topological distance, falling back to the overall diameter when no warhead
  is defined. A new **Interpret tab** gives med-chem read-outs computed from the decomposition +
  potency: **matched molecular pairs**, **linker-length SAR** with the optimum per congeneric
  series, **what tracks with potency**, and a **compare tool** — pick any two compounds and the
  atoms that differ are highlighted on each structure. The structural diff is now a
  **connectivity-aware maximum-common-substructure mapping** (a greedy bond-order-aware MCS
  grown from the distinctive atoms on both ligands, since RDKit.js here has no native MCS), so
  it catches **regioisomers and a group moved along the linker** — e.g. a gem-dimethyl that
  shifts position, which the old atom-environment multiset left unflagged. Matched pairs are
  found from this real difference rather than from fragment-string equality, and the region
  label is a **best-effort annotation flagged "auto — verify"** whenever the decomposition
  wasn't hand-set, so a mislabelled linker no longer silently reports a warhead change as a
  linker change. When reading drawn structures, Claude now **double-checks each structure
  against its page immediately** and corrects it (a second pass, slower but much more accurate —
  toggleable). A **"Load patent-style examples"** button loads an illustrative LRRK2 CRBN PROTAC
  series built from the WO 2025/072629 chemotype (benzimidazolone–glutarimide recruiter +
  indazole/pyrimidine warhead + PEG linker; synthetic DC₅₀/Dmax) to exercise all of the above.
- **`index-v6.html`** — v5 plus smarter region matching and a data-first scan.
  **Push-to-all now uses flood-fill splitting**: it matches your E3/POI *cores* (and
  the E3-ligase library) on every compound, then any ring system or substituent
  hanging off a core — a slight recruiter/warhead variation the template didn't
  match — is absorbed into *that ligand*, not the linker. The **linker is only the
  acyclic chain between E3 and POI**, so single-atom differences no longer leak into
  the linker. You can hold **several E3 and POI definitions** at once (define each
  variant once), and the **page-range box is read in order** — list the data-table
  pages first (e.g. `150-175, 60-110`) to match degradation data to compounds before
  the structures are read.
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
