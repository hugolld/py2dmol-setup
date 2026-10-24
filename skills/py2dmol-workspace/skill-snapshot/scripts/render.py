#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["py2Dmol @ git+https://github.com/sokrypton/py2Dmol.git@4a2397313eec1a7606093df19515158bd8ca939c"]
# ///
"""Build a self-contained py2Dmol viewer HTML page from a JSON spec (or CLI shorthand).

The HTML is the interchange format for headless export: it embeds every script,
structure and config the viewer needs, so `export.py` can open it in headless
Chromium and call the renderer's JS API (saveImage / startRecording).

PyPI's py2Dmol 1.6.5 predates the cartoon style, presets, and the saveImage JS
API, so this script installs py2Dmol from a pinned GitHub-main commit (uv
caches it after the first run; bump the pin when upstream lands fixes).

Usage:
    uv run scripts/render.py spec.json -o viewer.html
    uv run scripts/render.py --pdb 6MRR --style cartoon --color chain -o viewer.html
    uv run scripts/render.py --afdb Q5VSL9 --color plddt --pae -o viewer.html
    uv run scripts/render.py --file md_traj.pdb --autoplay --rotate -o viewer.html

Spec schema and full parameter reference: references/api.md in this skill.
"""

import argparse
import inspect
import json
import sys
from pathlib import Path

DEFAULT_VIEWER_ID = "py2dmol_export"  # deterministic id so export.py can address the renderer

VALID_STYLES = ("tube", "cartoon")
VALID_PRESETS = ("richardson", "ribbon", "3d")
VALID_COLORS = ("auto", "chain", "plddt", "rainbow", "ss", "entropy", "deepmind")
VALID_OUTLINES = ("none", "partial", "full")


def fail(msg: str) -> None:
    print(f"render.py: error: {msg}", file=sys.stderr)
    sys.exit(1)


def load_spec(args) -> dict:
    """Spec comes from a JSON file, or from CLI shorthand flags."""
    if args.spec and args.spec != "-":
        try:
            spec = json.loads(Path(args.spec).read_text())
        except FileNotFoundError:
            fail(f"spec file not found: {args.spec}")
        except json.JSONDecodeError as e:
            fail(f"spec file is not valid JSON: {e}")
    else:
        entries = []
        if args.pdb:
            entries.append({"type": "pdb", "id": args.pdb})
        if args.afdb:
            entries.append({"type": "afdb", "id": args.afdb})
        for f in args.file or []:
            entries.append({"type": "file", "path": f})
        if not entries:
            fail("no source given — pass a spec file, or one of --pdb/--afdb/--file")
        viewer = {"style": args.style or "tube"}
        if args.preset:
            viewer["preset"] = args.preset
        if args.color:
            viewer["color"] = args.color
        if args.size:
            viewer["size"] = args.size
        for key in ("colorblind", "rotate", "autoplay", "pae", "overlay"):
            if getattr(args, key):
                viewer[key] = True
        if args.contacts:
            entries[0]["contacts"] = args.contacts
        if args.scatter:
            entries[0]["scatter"] = args.scatter
        spec = {"viewer": viewer, "load": entries}
    if not isinstance(spec, dict):
        fail("spec root must be a JSON object")
    return spec


def check_viewer_kwargs(kwargs: dict, signature) -> dict:
    """Keep only keys that match the installed view() signature; fail loudly on typos."""
    params = set(signature.parameters) - {"self"}
    unknown = sorted(set(kwargs) - params)
    if unknown:
        fail(f"unknown viewer option(s) {unknown} — valid options: {sorted(params)}")
    if "style" in kwargs and kwargs["style"] not in VALID_STYLES:
        fail(f"invalid style {kwargs['style']!r} — expected one of {VALID_STYLES}")
    if "preset" in kwargs and kwargs["preset"] not in VALID_PRESETS:
        fail(f"invalid preset {kwargs['preset']!r} — expected one of {VALID_PRESETS}")
    if "color" in kwargs and isinstance(kwargs["color"], str) and kwargs["color"] not in VALID_COLORS:
        fail(f"invalid color mode {kwargs['color']!r} — expected one of {VALID_COLORS} "
             "(or a literal like \"red\" / \"#ff0000\" / {\"r\":255,\"g\":0,\"b\":0})")
    if "outline" in kwargs and kwargs["outline"] not in VALID_OUTLINES:
        fail(f"invalid outline {kwargs['outline']!r} — expected one of {VALID_OUTLINES}")
    if "size" in kwargs:
        kwargs["size"] = tuple(kwargs["size"])
    return kwargs


def apply_loads(viewer, entries: list) -> None:
    """Load each source into the viewer. show=False stops from_pdb/from_afdb from
    calling IPython display(), which is meaningless outside a notebook."""
    if not isinstance(entries, list) or not entries:
        fail("'load' must be a non-empty list of source objects")
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict) or "type" not in entry:
            fail(f"load[{i}] must be an object with a 'type' key")
        t = entry["type"]
        common = {k: entry[k] for k in ("chains", "name", "contacts", "scatter", "scatter_config") if k in entry}
        if t == "pdb":
            if "id" not in entry:
                fail(f"load[{i}] (pdb) needs an 'id', e.g. \"6MRR\" or \"1tim_AB\" for chains")
            viewer.from_pdb(entry["id"], use_biounit=entry.get("use_biounit", False), show=False, **common)
        elif t == "afdb":
            if "id" not in entry:
                fail(f"load[{i}] (afdb) needs a UniProt 'id', e.g. \"Q5VSL9\"")
            viewer.from_afdb(entry["id"], show=False, **common)
        elif t == "file":
            if "path" not in entry:
                fail(f"load[{i}] (file) needs a 'path'")
            if not Path(entry["path"]).is_file():
                fail(f"load[{i}] file not found: {entry['path']}")
            viewer.add_pdb(entry["path"], **common)
        else:
            fail(f"load[{i}] has unknown type {t!r} — expected 'pdb', 'afdb' or 'file'")


def apply_overrides(viewer, spec: dict) -> None:
    for o in spec.get("set_color", []):
        viewer.set_color(**o)
    for o in spec.get("set_sse", []):
        viewer.set_sse(**o)


def build_single(spec: dict, signature):
    import py2Dmol

    viewer_kwargs = check_viewer_kwargs(dict(spec.get("viewer", {})), signature)
    viewer_kwargs.setdefault("id", DEFAULT_VIEWER_ID)
    viewer = py2Dmol.view(**viewer_kwargs)
    apply_loads(viewer, spec.get("load"))
    apply_overrides(viewer, spec)
    if not any(obj.get("frames") for obj in viewer.objects):
        fail("viewer loaded no frames — check IDs/paths and network access to RCSB/AlphaFold DB")
    # _display_viewer returns the fragment show() would hand to Jupyter (styles,
    # config and data scripts, canvas div). Wrapping it in a minimal page makes
    # it a standalone document a browser can open directly.
    fragment = viewer._display_viewer(static_data=viewer.objects)
    vid = viewer.config.get("viewer_id", DEFAULT_VIEWER_ID)
    n_frames = sum(len(obj.get("frames", [])) for obj in viewer.objects)
    return [vid], fragment, n_frames


def build_grid(grid_spec: dict, signature):
    import importlib

    import py2Dmol
    import py2Dmol.viewer as viewer_mod

    # NB: py2Dmol.grid (attribute) is the factory FUNCTION — the __init__
    # from-import shadows the submodule — so grab the module via sys.modules.
    grid_mod = importlib.import_module("py2Dmol.grid")

    views = grid_spec.get("views")
    if not isinstance(views, list) or len(views) < 2:
        fail("'grid.views' must be a list of at least 2 view specs")
    g = py2Dmol.grid(
        cols=grid_spec.get("cols", 2),
        rows=grid_spec.get("rows"),
        gap=grid_spec.get("gap", 5),
        size=tuple(grid_spec["size"]) if grid_spec.get("size") else None,
    )
    # g.view() marks cells live (_is_live=True), so add()/from_pdb() emit
    # notebook-only incremental-update displays. Silence them; grid.show()
    # embeds the full static data anyway.
    viewer_mod.display = lambda h, **kw: None
    ids = []
    for i, sub in enumerate(views):
        viewer_kwargs = check_viewer_kwargs(dict(sub.get("viewer", {})), signature)
        viewer_kwargs.setdefault("id", f"py2dmol_grid_{i}")
        cell = g.view(**viewer_kwargs)
        apply_loads(cell, sub.get("load"))
        apply_overrides(cell, sub)
        ids.append(viewer_kwargs["id"])
    # g.show() composes the grid HTML (CSS grid wrapper + per-viewer fragments,
    # libs only in the first cell) but ends in IPython's display(). Intercept
    # that one call to capture the HTML instead of printing it to stdout.
    captured = []
    grid_mod.display = lambda h, **kw: captured.append(h.data if hasattr(h, "data") else str(h))
    g.show()
    if not captured:
        fail("grid produced no HTML (are all views empty?)")
    return ids, captured[0], len(views)


PAGE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>body {{ margin: 0; background: transparent; }}</style>
</head>
<body>
{body}
</body>
</html>
"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", nargs="?", help="path to spec JSON ('-' to rely on CLI flags)")
    ap.add_argument("-o", "--out", default="viewer.html", help="output HTML path (default: viewer.html)")
    ap.add_argument("--title", default="py2Dmol viewer", help="page <title>")
    # CLI shorthand (spec file wins where both exist)
    ap.add_argument("--pdb", help="RCSB PDB ID, e.g. 6MRR or 1tim_AB (chains)")
    ap.add_argument("--afdb", help="UniProt accession for AlphaFold DB, e.g. Q5VSL9")
    ap.add_argument("--file", action="append", help="local .pdb/.cif path (repeatable)")
    ap.add_argument("--style", choices=VALID_STYLES)
    ap.add_argument("--preset", choices=VALID_PRESETS)
    ap.add_argument("--color", help=f"color mode: {', '.join(VALID_COLORS)}")
    ap.add_argument("--size", type=int, nargs=2, metavar=("W", "H"))
    ap.add_argument("--colorblind", action="store_true")
    ap.add_argument("--rotate", action="store_true", help="auto-rotate (for turntable videos)")
    ap.add_argument("--autoplay", action="store_true", help="auto-play trajectory animation")
    ap.add_argument("--pae", action="store_true", help="fetch & show PAE matrix (afdb)")
    ap.add_argument("--overlay", action="store_true", help="draw all frames at once")
    ap.add_argument("--contacts", help="contacts file (.cst) or inline array for the source")
    ap.add_argument("--scatter", help="per-frame scatter CSV for the source")
    args = ap.parse_args()

    spec = load_spec(args)
    import py2Dmol  # fail early with a clear message if the git dep cannot resolve

    signature = inspect.signature(py2Dmol.view.__init__)

    if "grid" in spec:
        if spec.get("load"):
            fail("spec has both 'grid' and top-level 'load' — put loads inside grid.views[]")
        ids, body, count = build_grid(spec["grid"], signature)
        kind = f"grid of {count} viewers"
    else:
        ids, body, count = build_single(spec, signature)
        kind = f"{count} frame(s)"

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(PAGE.format(title=args.title, body=body))

    print(f"wrote {out} ({kind})")
    print(f"viewer id(s): {', '.join(ids)}")
    print(f"next: uv run scripts/export.py {out} -o <output.png|svg|mp4|gif|webm>")


if __name__ == "__main__":
    main()
