# py2Dmol Python API — verified reference

Verified against `sokrypton/py2Dmol` git main @ `4a23973` (self-reported 1.7.0,
2026-08-17). **Do not install py2Dmol from PyPI, whatever the version says.**
PyPI releases are silently divergent from git main at the JS layer: 1.6.5 has
no cartoon style at all, and 1.7.0 accepts the new `style=`/`preset=` Python
kwargs but ships the old renderer — no `saveImage`, no cartoon draw path — so
headless export breaks with no error pointing at the cause. Install from git,
pinned to a commit so behavior is reproducible and `uv run` doesn't refetch
HEAD every run (bump the pin when upstream lands fixes you want):

```
dependencies = ["py2Dmol @ git+https://github.com/sokrypton/py2Dmol.git@4a2397313eec1a7606093df19515158bd8ca939c"]
```

## Contents
- [view() constructor](#view-constructor)
- [Loading structures](#loading-structures)
- [Color & secondary-structure overrides](#overrides)
- [Contacts](#contacts)
- [Scatter plots](#scatter)
- [Grids](#grids)
- [State, custom payloads, live mode](#state-custom-live)
- [Spec schema](#spec-schema)
- [Escape-hatch template](#escape-hatch)
- [Known upstream gaps](#known-gaps)

## view constructor

`view` is a **class**; `py2Dmol.view(**kwargs)` constructs it.

| Parameter | Default | Notes |
|---|---|---|
| `size` | `(400, 400)` | canvas (w, h) px |
| `controls` / `box` | `True` | playback controls / bounding box |
| `color` | `"auto"` | mode: `auto, chain, plddt, rainbow, ss, entropy, deepmind` |
| `colorblind` | `False` | colorblind-safe palettes |
| `ss_palette` | `None` | for `color="ss"`: `pymol` (default), `jmol`, `jr1`, `jr2` |
| `style` | `"tube"` | `"tube"` or `"cartoon"` — the only two draw paths |
| `preset` | `None` | `richardson` \| `ribbon` \| `3d`; **implies style="cartoon"**; plain `style="cartoon"` → `richardson` |
| `smooth` | `None` | smooth shading; defaults False for cartoon, True otherwise |
| `thickness` | resolved | Å slab thickness; None → 0.7 (richardson) / 1.0 (3d) / 0 (flat) |
| `sheet_flat` | `None` | 0–1, damps β-pleat |
| `pencil` | `None` | 0–1, colored-pencil grain |
| `arrows` | `True` | β-strand arrowheads at C-term |
| `base_plates` | `None` | DNA/RNA base plates (on by default) |
| `detail` | `4` | cartoon subdivisions/residue, 2–8 |
| `fade` | `0` | 0–1 depth fade toward the page |
| `highlight` | `1.8` | specular lift (≥0) |
| `outline_tint` | resolved | 0=black ink, 1=element-tinted; 0.8 for richardson |
| `shadow` / `shadow_strength` | `True` / `0.5` | cast shadow |
| `shade` | `1.0` | directional shading 0–1 |
| `outline` | `"full"` | `none` \| `partial` \| `full` |
| `width` | `3.0` | line width |
| `ortho` | `0.5` | orthographic strength 0–1 |
| `bg` | `None` | `"white"` / `"black"` (3d preset defaults to black) |
| `rotate` | `False` | auto-rotate → turntable video |
| `autoplay` | `False` | play trajectory on load |
| `pae` / `pae_size` | `False` / `300` | PAE matrix panel (pair with `from_afdb`) |
| `scatter` / `scatter_size` | `None` / `300` | per-frame scatter panel |
| `overlay` | `False` | draw all frames simultaneously |
| `detect_cyclic` | `True` | cyclic peptide N–C bond detection |
| `persistence` | `True` | notebook cell behavior (ignore headless) |
| `id` | `None` | **custom viewer id** — use it: deterministic ids make headless export address the renderer without guessing |
| `cutoffs` | see notes | bond thresholds: `protein_bond` 5.0 (CA–CA), `nucleic_bond` 7.5 (C4′–C4′), `ligand_bond` 2.0 (heavy atoms) |

Colors are softened by a fixed 25% white mix (DeepMind palette excepted) —
there is no user-facing pastel control.

## Loading structures

```python
viewer.from_pdb(pdb_id, chains=None, name=None, align=True, use_biounit=False,
                biounit_name="1", load_ligands=True, contacts=None, scatter=None,
                color=None, ignore_ligands=None, show=None, scatter_config=None)
viewer.from_afdb(uniprot_id, chains=None, name=None, align=True, use_biounit=False,
                 biounit_name="1", load_ligands=True, scatter=None, color=None, show=None)
viewer.add_pdb(filepath, chains=None, name=None, paes=None, align=True,
               use_biounit=False, biounit_name="1", load_ligands=True,
               contacts=None, scatter=None, color=None, scatter_config=None)
```

- `from_pdb` fetches CIF from RCSB. Chain suffixes only on 4-char IDs:
  `1timA`, `1TIM_A`, `1tim_AB` (one chain per char), `1tim:A,B` (commas allow
  multi-char ids). UniProt-style accessions (`Q5VSL9`) are never mistaken for
  `ID+chains` because they start with a letter.
- `from_afdb` fetches AlphaFold DB; pass `view(pae=True)` to also fetch/show
  the PAE matrix.
- `add_pdb` reads a local `.pdb`/`.cif` path. **Multi-model files load every
  MODEL as an animation frame** (MD trajectories).
- `show=False` on `from_pdb`/`from_afdb` suppresses the automatic Jupyter
  `display()` — always pass it in headless scripts (`add_pdb` never auto-shows).
- Multiple `add_pdb(..., name="X")` calls create switchable objects.
- `align=True` superposes new objects onto the existing ones.

## Overrides

Five-level color priority, weakest → strongest: view `color=` < object < frame
< chain < position. An explicit literal always beats a mode.

```python
viewer.set_color("red", chain="A")
viewer.set_color("yellow", position=(0, 20))            # 0-based, inclusive range
viewer.set_color("red", chain="A", position=10, frame=0)
viewer.set_color({"type": "mode", "value": "plddt"}, name="obj1")  # object-level mode
viewer.set_sse("H", position=(20, 35))   # "H" helix | "E" strand | "C" loop | None = auto
viewer.set_sse("E", chain="B")
```

Literal colors: named (`"red"`), hex (`"#ff0000"`), or `{"r":255,"g":0,"b":0}`.

## Contacts

Colored lines between residues; line width follows weight.

- File (`.cst`), one per line — either form:
  - `idx1 idx2 weight [color]` (0-based indices)
  - `chain1 res1 chain2 res2 weight [color]`
- Array: `[idx1, idx2, weight]` or `[idx1, idx2, weight, {"r":255,"g":0,"b":0}]`

```python
viewer.add_pdb("complex.pdb", contacts="contacts.cst")
```

## Scatter

Per-frame 2D data (RMSD vs energy, PCA) synced to a trajectory; highlights the
current frame, click to jump.

```python
viewer = py2Dmol.view(scatter=True, scatter_size=300)
viewer.add_pdb("traj.pdb", scatter="data.csv",
               scatter_config={"xlabel": "RMSD (Å)", "ylabel": "Energy (kcal/mol)",
                               "xlim": [0, 10], "ylim": [-150, -90]})
```

Data: 2-column array/CSV with one row per frame; optional CSV header row
becomes axis labels.

## Grids

```python
with py2Dmol.grid(cols=2, rows=None, gap=5, size=None, controls=False, box=False) as g:
    g.view().from_pdb("1YNE")          # grid defaults: size/controls/box, overridable
    g.view(rotate=True).from_pdb("1BJP")
```

Grid composes one HTML page; only the first viewer embeds the JS libraries.
`render.py` builds grids via the explicit `Grid` class and intercepts the
final `display()` call to capture the HTML string.

## State, custom, live

```python
viewer.save_state("viz.json"); viewer2.load_state("viz.json")   # full reproducibility
viewer.add(coords, plddts, chains, position_types, pae=..., scatter=..., name=...)
```

`position_types`: `P` protein (CA trace), `D` DNA (C4′), `R` RNA (C4′), `L`
ligand (heavy atoms). Backbone and SS are rebuilt from the trace (PULCHRA-style
binning + real DSSP, Q3 ≈ 90%). Live mode (`show()` before `add()`) streams
frames — useful in notebooks, not needed headless.

## Spec schema

Top level:

| Key | Type | Meaning |
|---|---|---|
| `viewer` | object | any `view()` option from the table above, plus `id` (default `py2dmol_export`) |
| `load` | list | sources, in order (below) — mutually exclusive with `grid` |
| `set_color` / `set_sse` | list | each item's keys are the method's kwargs |
| `grid` | object | `cols`, `rows`, `gap`, `size`, `views: [{viewer, load, set_color, set_sse}]` (cell ids: `py2dmol_grid_N`) |
| `title` | str | page `<title>` |

`load` entry by `type`:

- `pdb`: `id` (may carry chain suffix), `use_biounit`, `chains`, `name`,
  `contacts`, `scatter`, `scatter_config`
- `afdb`: `id` (UniProt), `chains`, `name`, `scatter` (PAE via `viewer.pae`)
- `file`: `path` (`.pdb`/`.cif`, multi-model = animation), `name`, `contacts`,
  `scatter`, `scatter_config`

`render.py` validates against the installed `view.__init__` signature, so new
upstream parameters work in specs without skill updates; unknown keys fail
with the valid list.

## Escape hatch

```python
# /// script
# requires-python = ">=3.10"
# dependencies = ["py2Dmol @ git+https://github.com/sokrypton/py2Dmol.git@4a2397313eec1a7606093df19515158bd8ca939c"]
# ///
import py2Dmol

viewer = py2Dmol.view(size=(800, 800), style="cartoon", color="chain", id="py2dmol_export")
viewer.from_pdb("6MRR", show=False)          # or add(...) with raw coordinates
viewer.set_color("red", position=(50, 60))
html = viewer._display_viewer(static_data=viewer.objects)   # the fragment show() displays
page = (f"<!DOCTYPE html><html><head><meta charset='utf-8'></head>"
        f"<body style='margin:0'>{html}</body></html>")
open("viewer.html", "w").write(page)
# then: uv run scripts/export.py viewer.html -o fig.png --dpi 300
```

`_display_viewer(static_data, include_libs=True)` returns the self-contained
fragment (styles + config/data scripts + canvas div) — wrap it in a minimal
page as above. `export.py` accepts any page containing a py2Dmol viewer.

## Known gaps

- **MSA panels are documented upstream** (technical_readme: `add_msa(data,
  format='a3m'|'fasta'|'stockholm', start, end)`) **but not present in the
  code** at this commit — no `add_msa` method, no MSA resource file. Re-check
  when a new release lands; until then use contacts/scatter for annotations.
- No Python-side export API — all export goes through the browser pipeline
  (see [export-pipeline.md](export-pipeline.md)).
