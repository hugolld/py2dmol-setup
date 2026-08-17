# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This repo develops the **py2dmol agent skill** — a Claude Code skill wrapping the [py2Dmol](https://github.com/sokrypton/py2Dmol) Python library (2D protein/DNA/RNA visualization) to produce slide/movie-ready images and animations. Deployment target is a **Claude Code plugin** primarily, with future compatibility with npx-based skill runners. Pre-development: no code exists yet.

## Decided conventions (2026-08-17)

- Layout: canonical skill source at `skills/py2dmol/` (plugin-ready; add `.claude-plugin/plugin.json` when packaging). During development, symlink `.claude/skills/py2dmol -> ../../skills/py2dmol` so sessions here can invoke it live.
- Environment: uv project at repo root for development (`uv sync`, `uv run`). Scripts shipped inside the skill must be **PEP 723 standalone** (`# /// script` inline metadata) so they run via `uv run` in any target project without this repo's env.
- Skill must support all four input types: PDB IDs (RCSB), AlphaFold DB (UniProt), local `.pdb`/`.cif` files (incl. multi-model MD trajectories), MSA/contacts data.
- SKILL.md frontmatter: standard `name` + `description` only (cross-runner compatibility); avoid Claude-specific fields in the core path.

## py2Dmol facts (verified against sokrypton/py2Dmol @ main, 2026-08-17)

- pip package name is `py2Dmol` (capital D). It is Jupyter-oriented: `show()` renders via IPython `display(HTML(...))`.
- **No headless export exists in the Python API** — PNG/SVG/video export is browser-side JS. The headless pipeline therefore is:
  1. `viewer._display_viewer(static_data=viewer.objects)` returns the complete self-contained HTML string (what `show()` renders) — write it to a file to bypass Jupyter.
  2. In a browser (Playwright works), `window.py2dmol_viewers[viewerId].renderer` exposes `saveImage({format: 'png'|'svg'|'svgz', dpi})`, `startRecording()`, `stopRecording()` — call these and capture the triggered download.
- Exports are **always transparent-background** (by design; don't bake in a white rect). PNG `dpi` is a render scale: 300 dpi on a 600 px view → 1875×1875. Rotate/Draw animations record as **WebM** — convert with ffmpeg if a slide tool needs MP4.
- Styles: `tube` (default), `cartoon` (presets `richardson` default, `ribbon`, `3d`). Color modes: `auto`, `chain`, `plddt`, `rainbow`, `ss`, `entropy`, `deepmind`; per-target overrides via `set_color(color, chain=, position=, frame=)` and `set_sse("H"|"E"|"C"|None, ...)`.
- Loaders: `from_pdb('6MRR')` downloads CIF from RCSB (4-char IDs take chain suffixes like `1tim_AB`); `from_afdb('Q5VSL9')` fetches AlphaFold DB (optionally with PAE). Multi-model PDB/mmCIF files load as animation frames; `py2Dmol.grid()` makes galleries.
