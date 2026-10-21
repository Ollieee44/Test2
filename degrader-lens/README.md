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
- **Ingestion & extraction.** Load the bundled sample set, paste or upload **CSV**
  (`id, smiles, dc50_nm, dmax_pct, …`), a **SMILES list**, or an **SDF**; set the
  warhead scaffold; and run the **patent-text extractor**, which pulls compound
  identifiers and reported IC₅₀ / DC₅₀ / Dmax values and merges them onto matching
  compounds (unmatched values are kept as data-only rows).

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

## Scope and limitations

- Turning a **drawn structure in a patent image** into SMILES needs optical
  chemical-structure recognition (e.g. `DECIMER`, `MolScribe`); run that as a
  separate step and paste its SMILES output here or into a CSV. In-browser OCSR is
  not attempted, and the tool is honest about that rather than guessing structures.
- Fully automatic warhead/linker splitting of an arbitrary molecule is a hard
  problem; region-based SAR is accurate when a shared warhead scaffold is supplied.
- Descriptors are 2D/topological estimates (cLogP is Crippen), not measured values.

Structure handling uses [RDKit.js](https://github.com/rdkit/rdkit-js) 2025.3.4
(RDKit 2025.03). PDB-free, offline-capable once the WASM module is cached.
