# Headless export pipeline — internals & troubleshooting

Why this pipeline exists, what exactly happens in `export.py`, and how to fix
the failures it can hit. Read when exports misbehave or when adapting the
scripts.

## Contents
- [Architecture](#architecture)
- [The JS bridge](#js-bridge)
- [Still images: saveImage semantics](#stills)
- [Video: recording semantics](#video)
- [MP4/GIF conversion](#conversion)
- [Grids and multi-viewer pages](#grids)
- [Troubleshooting](#troubleshooting)

## Architecture

```
render.py                                export.py
┌──────────────────────┐                ┌─────────────────────────────────┐
│ py2Dmol.view(id=...)  │  fragment      │ headless Chromium (Playwright)  │
│ from_pdb(show=False)  │ ────────────►  │ page.goto(file://viewer.html)   │
│ _display_viewer(      │  wrapped in    │ wait for window.py2dmol_viewers │
│   static_data=objects)│  minimal page  │ call renderer JS -> download    │
└──────────────────────┘                │ convert webm via ffmpeg         │
                                        └─────────────────────────────────┘
```

`show()` in py2Dmol ends in IPython's `display(HTML(...))`; the HTML string it
displays comes from `viewer._display_viewer(static_data=viewer.objects)`. That
string embeds everything — minified renderer, per-viewer config under
`window.py2dmol_configs[viewer_id]`, serialized frames under
`window.py2dmol_staticData[viewer_id]` — so the page is portable and needs no
network. `render.py` wraps the fragment in a minimal HTML document because
`_display_viewer` returns a fragment, not a full page.

## JS bridge

Inside the page:

```js
window.py2dmol_viewers            // registry of live viewer instances, keyed by id
window.py2dmol_viewers[id].renderer      // Pseudo3DRenderer
renderer.saveImage({format: 'png', dpi: 300})   // or {format: 'svg'} / {format: 'svgz'}
renderer.startRecording()
renderer.stopRecording()
```

Setting `id` in `view(id=...)` (render.py defaults it to `py2dmol_export`,
grid cells to `py2dmol_grid_N`) makes the registry key deterministic. All
three calls trigger a browser download, which Playwright captures via
`expect_download`. Readiness = `Object.keys(window.py2dmol_viewers).length > 0`
plus a settle delay.

## Stills

- **Transparent background, always** — exports are the structure alone; never
  bake a white/black rect. Checkered appearance in Preview/Finder = alpha, not
  a bug. To preview, place over a slide-colored rectangle.
- **`dpi` is a render scale, not upscaling**: the renderer re-renders at output
  size, so 300 dpi on a 600 px view yields 1875×1875 with genuinely finer
  curves. Pixel-defined quantities (outline width, selection ink) are scaled
  to keep screen proportions.
- SVG keeps the pencil grain as an `feTurbulence` filter and gradient
  shading — not a flat-color downgrade. `svgz` is gzipped SVG.
- Draw-mode stills are PNG-only by design (off-register watercolor doesn't
  survive vectorization).

## Video

- Recordings come off the canvas at **canvas size** — dpi does not apply. For
  higher-resolution video, render with a larger `size`.
- `rotate=True` recordings cover exactly one revolution and loop seamlessly
  (0→360° exclusive); export.py stops after `--seconds` and the JS auto-stop
  whichever comes first.
- `autoplay` trajectory recordings run until `--seconds` elapses
  (`stopRecording()` then fires the download).
- Native output is **WebM** (MediaRecorder). `startRecording` requires a
  loaded object (`currentObjectName`) — it warns and no-ops on an empty
  viewer.
- The **Draw** (hand-drawn watercolour) animation is a Style-panel feature
  driven from the live UI; it is not currently exposed as a renderer method
  to call headlessly. Recordings of rotate/trajectory are the scriptable paths.

## Conversion

`export.py` prefers system `ffmpeg` if on PATH, else the static build bundled
with the `imageio-ffmpeg` wheel (no system install needed).

- MP4: `-c:v libx264 -pix_fmt yuv420p -crf 18 -movflags +faststart` — plays in
  PowerPoint, Keynote, browsers, and Slack/Zoom screen shares.
- GIF: `fps=N` + `palettegen`/`paletteuse` (bayer dither), `-loop 0`.
- The native `.webm` is kept beside mp4/gif output (drop with `--no-webm`).

## Grids

`saveImage` exports one viewer. For a whole grid page use `export.py --page`:
a full-page Playwright screenshot with `omit_background` (transparent) and
`--scale` (device scale factor; the canvas is `devicePixelRatio`-aware so 2–3×
stays crisp). For per-cell 300-dpi exports instead, export each `py2dmol_grid_N`
id with `--viewer-id` — sharper, but N separate files.

## Troubleshooting

| Symptom | Cause → fix |
|---|---|
| `no py2dmol viewer appeared within 30s` | HTML opened before data scripts ran, or spec loaded nothing → re-run `render.py`, watch its errors; check the page manually in a browser |
| Download never fires (still) | `saveImage` guarded (no object loaded) → viewer HTML is empty; verify `render.py` reported frames |
| Recording is a static image | neither `rotate` nor `autoplay` in viewer config → add one (export.py warns) |
| Blurry grid export | raise `--scale` to 3; or per-cell `--viewer-id` export at dpi |
| White background in PNG | expected: it's transparent — the viewer you checked it in painted white |
| `Executable doesn't exist` / chromium error | no system Chrome/Edge and bundled Chromium missing — export.py auto-installs it (`playwright install chromium`, ~150 MB); needs network. Installing Google Chrome avoids the download entirely |
| py2Dmol import / cartoon errors | stale PyPI install — PyPI 1.7.0 takes the `style=`/`preset=` kwargs but ships the old JS (no `saveImage`, no cartoon renderer); the skill pins `py2Dmol @ git+<commit>`. `uv cache clean py2dmol` if a stale wheel sticks |
| `renderer.saveImage is not a function` | PyPI wheel in the env (see above) — force the pinned git dep |
| RCSB/AFDB fetch fails in render.py | network/ID typo — 4-char IDs (optionally with chain suffix) for `from_pdb`, UniProt accessions for `from_afdb` |
| mp4 conversion fails | read the ffmpeg stderr printed by export.py; try system ffmpeg (`brew install ffmpeg`) if the bundled build lacks a codec |
| Playwright works but canvas blank at high dpi | very large `size` × `dpi` exceeds canvas limits → lower dpi or size (300 dpi @ 900 px ≈ 2812 px is safe) |
