---
name: py2dmol
description: Publication-quality 2D figures and animations of protein, DNA, and RNA structures using py2Dmol. Use this skill whenever the user wants to visualize a molecular structure — render a PDB ID, AlphaFold/UniProt model, local .pdb/.cif file, or MD trajectory as a slide-ready transparent PNG/SVG or an MP4/WebM/GIF animation (rotation turntable, trajectory playback), color by chain, pLDDT, rainbow, or secondary structure, draw contact maps, or build structure galleries — even if they never say "py2Dmol".
---

# py2Dmol — slide-ready 2D structure figures & animations

Renders 2D (pseudo-3D) cartoons of proteins and nucleic acids that look like
journal figures: Jane Richardson-style hand-drawn cartoons, tube traces,
pLDDT/chain/rainbow coloring, transparent backgrounds at high DPI, and
turntable or trajectory animations as video.

## How it works

py2Dmol is Jupyter-oriented with **no Python-side export** — PNG/SVG/video are
produced by JavaScript inside a browser. The skill therefore works in two
stages:

```
spec.json ──render.py──> viewer.html ──export.py──> fig.png / fig.svg / anim.mp4 / anim.gif
```

`render.py` builds a fully self-contained HTML page (structures, config and
scripts embedded; deterministic viewer id). `export.py` opens it in headless
Chromium and calls the renderer's JS API (`saveImage`, `startRecording`).
Keeping the HTML as an artifact means you can re-export at different DPI or
video settings without re-fetching structures from RCSB/AlphaFold DB.

Both scripts are PEP 723 standalone — run them with `uv run`, which resolves
their dependencies themselves. `render.py` installs py2Dmol from GitHub main
because the PyPI release (1.6.5) predates the cartoon style and the `saveImage`
export API. `export.py` drives an installed system Chrome/Edge when present;
only on machines with neither does it download Playwright's Chromium (~150 MB,
one time).

## Quick start

The common case is two commands and zero styling decisions — a bare ID uses
the publication default (cartoon · richardson · chain · 800×800):

```bash
# publication figure of a PDB entry: transparent 300-dpi PNG (~2500×2500)
uv run scripts/render.py --pdb 6MRR -o viewer.html
uv run scripts/export.py viewer.html -o 6mrr.png      # same HTML again → -o 6mrr.svg

# AlphaFold model, pLDDT colors + PAE matrix
uv run scripts/render.py --afdb Q5VSL9 --color plddt --pae -o viewer.html
uv run scripts/export.py viewer.html -o q5vsl9.png --page   # --page: includes the PAE panel

# MD trajectory (multi-model file) as slide-safe MP4
uv run scripts/render.py --file traj.pdb --autoplay -o viewer.html
uv run scripts/export.py viewer.html -o traj.mp4 --speed 200    # duration = frames × speed
```

When the user names parameters, override exactly those pieces with styling
flags (`--style tube --width 2.5 --outline full`, …) or `--set key=value` for
any other option — table below. For multiple sources, color overrides,
contacts, scatter plots, grids: write a spec file — schema below and in
[references/api.md](references/api.md).

## Choosing style and color

| Goal | style | preset | color |
|---|---|---|---|
| Journal-figure look (default choice) | cartoon | richardson (default) | chain |
| Clean minimal ribbons | cartoon | ribbon | ss |
| Solid shaded, dark background | cartoon | 3d | ss or rainbow |
| Topology overview / C-alpha traces | tube | — | rainbow |
| Confidence display (AlphaFold) | cartoon | richardson | plddt |
| Multi-chain complexes | cartoon | richardson | chain |

### Styling knobs

Each flag overrides exactly one piece of the default; everything unflagged
stays. `--set key=value` reaches every other `view()` option (value is
JSON-parsed): `--set fade=0.3 --set shadow=false --set pae_size=800`.

| Ask | flag | spec kwarg | notes (style defaults) |
|---|---|---|---|
| cartoon / tube | `--style` | `style` | presets pair with cartoon only |
| line weight | `--width` | `width` | 2.0 cartoon / 3.0 tube |
| outlines | `--outline none\|partial\|full` | `outline` | `full` by default |
| thicker elements | `--thickness` | `thickness` | cartoon only (0.7 richardson) |
| flatter β-sheets | `--sheet-flat` | `sheet_flat` | cartoon only, 0–1 |
| hand-drawn grain | `--pencil` | `pencil` | 0–1; 1.0 cartoon / 0 tube |
| depth fade | — | `fade` | 0–1 toward the page |
| cast shadow | — | `shadow`, `shadow_strength` | on / 0.5 |

Nucleic-acid duplexes get base plates automatically. py2Dmol's own spec
default `size=(400,400)` still applies to spec files; the shorthand defaults
to 800×800 precisely so bare-ID output is publication-sized (300 dpi →
~2500 px).

Explicit `set_color` entries always win over the color mode; use them to
highlight mutations, domains, or ligands.

## The spec file

```jsonc
{
  "viewer": {                       // any py2Dmol.view() option (references/api.md)
    "size": [800, 800],
    "style": "cartoon",             // "tube" | "cartoon"
    "preset": "richardson",         // "richardson" | "ribbon" | "3d" (implies cartoon)
    "color": "chain",               // auto|chain|plddt|rainbow|ss|entropy|deepmind
    "colorblind": true,
    "rotate": false,                // true = turntable video
    "autoplay": true                // play trajectory on load
  },
  "load": [                         // one or more sources, added in order
    { "type": "pdb",  "id": "1tim_AB", "use_biounit": true },
    { "type": "afdb", "id": "Q5VSL9" },         // viewer.pae: true fetches the PAE matrix
    { "type": "file", "path": "sim.pdb", "name": "sim1",
      "contacts": "contacts.cst",               // or [[i, j, weight, [r,g,b]], ...]
      "scatter": "rmsd.csv",                    // per-frame CSV: two columns, optional header
      "scatter_config": { "xlabel": "RMSD (Å)" } }
  ],
  "set_color": [ { "color": "red", "chain": "A", "position": [20, 35] } ],
  "set_sse":    [ { "sse": "H", "position": [40, 60] } ]   // "H"|"E"|"C"|null
}
```

`"grid"` replaces `load` for galleries: `{"grid": {"cols": 2, "size": [300,
300], "views": [{"viewer": {...}, "load": [...]}, ...]}}` — export with
`--page --scale 2` (or export cells individually via their
`py2dmol_grid_N` ids).

## Exporting

- `fig.png --dpi 300` — transparent PNG, re-rendered at output size (dpi buys
  finer geometry, not upsampling)
- `fig.svg` / `fig.svgz` — vector; keeps pencil grain and gradient shading
- `anim.mp4 --seconds 10` — H.264 yuv420p + faststart (safe for
  PowerPoint/Keynote); native `.webm` kept alongside (`--no-webm` to drop)
- `anim.gif --fps 15` — paletted, for embeds
- `--viewer-id ID` picks one viewer on a multi-viewer page; `--page` captures
  the whole page (grids)
- rotate recordings cover exactly one seamless-looping revolution; trajectory
  recordings are **frame-driven**: duration = frames × max(50, `--speed`) ms
  and self-stop — `--seconds` only caps the wait, `--speed` changes playback
  (40 frames × 200 ms = 8 s)
- PNG `dpi` is clamped by the renderer to [36, 1200]
- PAE panels sit outside the structure canvas — export PAE figures with
  `--page`, and pass `pae_size` (default 300) for a bigger matrix

## Workflow

1. Classify the request: a bare ID with no styling wishes → shorthand with no
   flags (the publication default IS the deliverable). Parameters named →
   override exactly those via flags/`--set`. Animation → `rotate` (turntable)
   or `autoplay` (trajectory) + mp4 with `--speed`. Comparison → grid.
2. Write the spec (or shorthand), render, export. Check what `render.py`
   prints — it names the viewer id and suggests the export command.
3. Verify the result before declaring done: PNG dimensions scale with dpi
   (printed by `export.py`), file is multi-MB at 300 dpi, background is
   transparent. View the image yourself when uncertain about aesthetics.
4. Iterate on styling by editing the spec and re-rendering — structure
   fetches are the slow part and only happen in `render.py`.

## Beyond the spec (escape hatch)

The spec covers declarative cases. For custom `add()` payloads (mixed
protein/DNA/ligand systems built from raw coordinates), live-mode tricks, or
parameters added upstream after this skill was written, write a one-off
PEP 723 script following the template in [references/api.md](references/api.md)
— build the viewer, then dump the page the same way `render.py` does and feed
it to `export.py` unchanged. `export.py` works with any HTML containing a
py2Dmol viewer, not just this skill's output.

## References

- [references/api.md](references/api.md) — complete verified Python API, spec
  schema, contact/MSA/scatter formats, escape-hatch template
- [references/export-pipeline.md](references/export-pipeline.md) — headless
  internals, DPI/transparency semantics, recording details, troubleshooting
- [references/cookbook.md](references/cookbook.md) — task → spec recipes
  (pLDDT figure, trajectory movie, gallery, contacts, highlights)
