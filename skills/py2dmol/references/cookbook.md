# Cookbook — task → spec recipes

Copy-paste starting points. Save the JSON as `spec.json`, then:

```bash
uv run scripts/render.py spec.json -o viewer.html
uv run scripts/export.py viewer.html -o <output>
```

Recipe 1 needs no spec at all — the CLI shorthand's default IS that recipe:
`uv run scripts/render.py --pdb 4HHB -o viewer.html`. Specs shine for the
multi-source/override cases below.

## Contents
- [1. Journal-style publication figure](#1-journal-style-publication-figure)
- [2. AlphaFold confidence figure (pLDDT + PAE)](#2-alphafold-confidence-figure)
- [3. MD trajectory movie](#3-md-trajectory-movie)
- [4. Rotation turntable video](#4-rotation-turntable-video)
- [5. Structure gallery (grid)](#5-structure-gallery-grid)
- [6. Contact map on a complex](#6-contact-map)
- [7. Mutation / domain highlighting](#7-highlighting)
- [8. Nucleic-acid duplex](#8-nucleic-acid-duplex)
- [9. Comparing two trajectories](#9-comparing-trajectories)

## 1. Journal-style publication figure

Richardson hand-drawn look, chain colors, 300 dpi PNG + SVG.

```json
{
  "viewer": { "size": [800, 800], "style": "cartoon", "preset": "richardson", "color": "chain" },
  "load": [ { "type": "pdb", "id": "4HHB", "use_biounit": true } ]
}
```

Export both formats from one HTML: `... -o hemoglobin.png` then `... -o
hemoglobin.svg`. For a cleaner machine-generated look use `"preset": "ribbon"`;
for maximum minimalism `"style": "tube", "color": "rainbow"`.

## 2. AlphaFold confidence figure

```json
{
  "viewer": { "size": [700, 700], "style": "cartoon", "preset": "richardson",
              "color": "plddt", "pae": true },
  "load": [ { "type": "afdb", "id": "Q5VSL9" } ]
}
```

pLDDT palette: dark blue ≥90, light blue 70–90, yellow 50–70, orange <50.
`colorblind: true` switches to a perceptually uniform ramp.

## 3. MD trajectory movie

Multi-model `.pdb`/`.cif` → every MODEL becomes a frame. MP4 for slides:

```json
{
  "viewer": { "size": [700, 700], "style": "cartoon", "preset": "ribbon",
              "color": "ss", "autoplay": true },
  "load": [ { "type": "file", "path": "md_traj.pdb" } ]
}
```

`uv run scripts/export.py viewer.html -o traj.mp4 --speed 200` — duration
is frame-driven (frames × max(50, speed) ms, self-stopping), so pick `--speed`
for the length you want; `--seconds` is just a safety cap.
Add per-frame scatter (RMSD/energy) to the load entry:
`"scatter": "analysis.csv", "scatter_config": {"xlabel": "RMSD (Å)", "ylabel": "Energy"}`.

## 4. Rotation turntable video

```json
{
  "viewer": { "size": [700, 700], "style": "cartoon", "preset": "richardson",
              "color": "chain", "rotate": true },
  "load": [ { "type": "pdb", "id": "1TIM" } ]
}
```

`... -o turntable.mp4` — exactly one seamless-looping revolution; also try
`"preset": "3d", "bg": "black"` for a rendered-object look.

## 5. Structure gallery (grid)

```json
{
  "grid": {
    "cols": 2, "size": [400, 400],
    "views": [
      { "viewer": { "style": "cartoon", "color": "chain" }, "load": [ { "type": "pdb", "id": "1YNE" } ] },
      { "viewer": { "style": "cartoon", "color": "chain" }, "load": [ { "type": "pdb", "id": "1BJP" } ] },
      { "viewer": { "style": "tube", "color": "rainbow" },  "load": [ { "type": "pdb", "id": "9D2J" } ] },
      { "viewer": { "style": "cartoon", "color": "plddt" }, "load": [ { "type": "afdb", "id": "Q5VSL9" } ] }
    ]
  }
}
```

`uv run scripts/export.py viewer.html -o gallery.png --page --scale 2`
(transparent full-page capture). Sharper alternative: per-cell
`--viewer-id py2dmol_grid_2 -o cell3.png --dpi 300`.

## 6. Contact map

```json
{
  "viewer": { "size": [700, 700], "style": "cartoon", "color": "chain" },
  "load": [ { "type": "file", "path": "complex.pdb", "contacts": "contacts.cst" } ]
}
```

`contacts.cst` — one per line, `idx1 idx2 weight [color]` (0-based) or
`chain1 res1 chain2 res2 weight [color]`. Or inline:
`"contacts": [[10, 45, 1.0], [12, 60, 0.5, {"r": 255, "g": 0, "b": 0}]]`.
Line width follows weight.

## 7. Highlighting

Explicit colors always beat the mode — highlight without losing context:

```json
{
  "viewer": { "size": [800, 800], "style": "cartoon", "preset": "richardson", "color": "chain" },
  "load": [ { "type": "pdb", "id": "6MRR" } ],
  "set_color": [ { "color": "red", "chain": "A", "position": [455, 475] },
                 { "color": "#222222", "chain": "B", "position": [30, 41] } ],
  "set_sse": [ { "sse": "H", "position": [480, 500] } ]
}
```

Positions are 0-based residue indices within the object. Combine with the
escape hatch ([api.md](api.md#escape-hatch)) for label-level control.

## 8. Nucleic-acid duplex

DNA/RNA render with base plates automatically; C4′ trace drives geometry
(base orientation from a fitted table — a rare `anti`/`syn` ambiguity can
flip an unpaired base).

```json
{
  "viewer": { "size": [700, 700], "style": "cartoon", "preset": "ribbon",
              "color": "chain", "outline": "partial" },
  "load": [ { "type": "pdb", "id": "1BNA" } ]
}
```

## 9. Comparing trajectories

Two named objects in one viewer (dropdown in interactive use; overlays via
`"overlay": true` for a double-exposure still):

```json
{
  "viewer": { "size": [700, 700], "style": "tube", "color": "chain",
              "autoplay": true, "overlay": false },
  "load": [ { "type": "file", "path": "sim1.pdb", "name": "wild type" },
            { "type": "file", "path": "sim2.pdb", "name": "mutant" } ]
}
```

`align: true` (default) superposes objects — for RMSD-fair comparisons keep it
on. A single-frame overlay still: `"overlay": true` + PNG export.
