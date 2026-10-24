#!/usr/bin/env python3
"""Objective checks for py2dmol skill eval outputs.

Usage: uv run --with numpy check_outputs.py <outputs_dir>
Prints a JSON array of {text, passed, evidence} for every assertion it can
check programmatically. Visual assertions (cartoon style, coloring scheme,
PAE visibility) are graded separately by viewing the images.
"""
import hashlib
import json
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path


def png_info(p: Path):
    with open(p, "rb") as f:
        h = f.read(33)
    if h[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    w, hh = struct.unpack(">II", h[16:24])
    return {"w": w, "h": hh, "color_type": h[25]}  # 6 = RGBA


def ffprobe(p: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=codec_name,pix_fmt,width,height:format=duration",
         "-of", "json", str(p)],
        capture_output=True, text=True)
    if out.returncode != 0:
        return {}
    d = json.loads(out.stdout or "{}")
    s = (d.get("streams") or [{}])[0]
    s["duration"] = float(d.get("format", {}).get("duration") or 0)
    return s


def frame_sig(p: Path, frac: float) -> str:
    dur = ffprobe(p).get("duration") or 0
    t = max(0.1, dur * frac)
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", str(t), "-i", str(p),
                          "-vframes", "1", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                         capture_output=True).stdout
    return hashlib.md5(raw).hexdigest()


def main() -> None:
    outdir = Path(sys.argv[1])
    pngs = sorted(outdir.glob("*.png"))
    svgs = sorted(outdir.glob("*.svg"))
    mp4s = sorted(outdir.glob("*.mp4"))
    results = []

    def add(text, passed, evidence):
        results.append({"text": text, "passed": bool(passed), "evidence": evidence})

    if "publication-still" in str(outdir) or "bare-id" in str(outdir) or len(pngs) + len(svgs) >= 2:
        if pngs:
            info = png_info(pngs[0])
            if info:
                add("PNG at least 2000x2000 pixels", min(info["w"], info["h"]) >= 2000,
                    f"{info['w']}x{info['h']}")
                add("PNG has alpha channel (RGBA)", info["color_type"] == 6,
                    f"color_type={info['color_type']}")
        else:
            add("PNG at least 2000x2000 pixels", False, "no PNG in outputs")
            add("PNG has alpha channel (RGBA)", False, "no PNG in outputs")
        if svgs:
            sz = svgs[0].stat().st_size
            add("SVG exists and is non-trivial (>10 KB)", sz > 10_000, f"{sz} bytes")
        else:
            add("SVG exists and is non-trivial (>10 KB)", False, "no SVG in outputs")

    if "afdb" in str(outdir):
        if pngs:
            info = png_info(pngs[0])
            if info:
                long_side = max(info["w"], info["h"])
                add("PNG long side >= 2000 px", long_side >= 2000, f"{info['w']}x{info['h']}")
                add("Image wider than tall (PAE alongside, ratio > 1.3)",
                    info["w"] / max(1, info["h"]) > 1.3,
                    f"ratio={info['w'] / max(1, info['h']):.2f}")
        interp = outdir / "interpretation.md"
        if interp.exists():
            txt = interp.read_text()
            add("interpretation.md cites specific regions",
                bool(re.search(r"\b\d{2,4}\b|-|\bNTD\b|\bCTD\b|domain|termin", txt)) and len(txt) > 200,
                f"{len(txt)} chars")
            add("interpretation.md identifies a low-confidence/disordered segment",
                bool(re.search(r"disorder|low[- ]confidence|unstructured|poorly", txt, re.I)),
                "keyword match" if re.search(r"disorder|low[- ]confidence|unstructured|poorly", txt, re.I) else "no match")
        else:
            add("interpretation.md cites specific regions", False, "missing interpretation.md")
            add("interpretation.md identifies a low-confidence/disordered segment", False, "missing interpretation.md")

    if "trajectory" in str(outdir) or mp4s:
        if mp4s:
            mp4 = mp4s[0]
            sz = mp4.stat().st_size
            add("MP4 exists, >100 KB", sz > 100_000, f"{sz/1e6:.2f} MB")
            info = ffprobe(mp4)
            add("MP4 is H.264 yuv420p",
                info.get("codec_name") == "h264" and info.get("pix_fmt") == "yuv420p",
                f"codec={info.get('codec_name')}, pix_fmt={info.get('pix_fmt')}")
            add("MP4 even width/height",
                info.get("width", 0) % 2 == 0 and info.get("height", 0) % 2 == 0,
                f"{info.get('width')}x{info.get('height')}")
            add("MP4 duration 6-12 s (~8 s requested; requires playback-speed control)",
                6 <= info.get("duration", 0) <= 12,
                f"{info.get('duration', 0):.1f}s")
            if info.get("duration", 0) > 1 and shutil.which("ffmpeg"):
                s1, s2 = frame_sig(mp4, 0.25), frame_sig(mp4, 0.75)
                add("Video animates (25% frame differs from 75% frame)", s1 != s2,
                    "frames differ" if s1 != s2 else "identical frames")
        else:
            add("MP4 exists, >100 KB", False, "no MP4 in outputs")
        if pngs:
            info = png_info(pngs[0]) if pngs else None
            add("PNG long side >= 2000 px",
                info and max(info["w"], info["h"]) >= 2000,
                f"{info['w']}x{info['h']}" if info else "no PNG")
        else:
            add("PNG long side >= 2000 px", False, "no PNG in outputs")

    if "custom-params" in str(outdir):
        if pngs:
            info = png_info(pngs[0])
            if info:
                add("PNG long side >= 2000 px", max(info["w"], info["h"]) >= 2000,
                    f"{info['w']}x{info['h']}")
                add("PNG has alpha channel (RGBA)", info["color_type"] == 6,
                    f"color_type={info['color_type']}")
        else:
            add("PNG long side >= 2000 px", False, "no PNG in outputs")
            add("PNG has alpha channel (RGBA)", False, "no PNG in outputs")
        htmls = sorted(outdir.glob("*.html"))
        if htmls:
            m = re.search(r"window\.py2dmol_configs\[[^\]]*\] = (\{[^;]*\})", htmls[0].read_text())
            rend = (json.loads(m.group(1)) if m else {}).get("rendering", {})
            add('Viewer HTML config pins style "tube"', rend.get("style") == "tube",
                f"style={rend.get('style')!r}")
            w = rend.get("width")
            add("Viewer HTML config pins width 2.5 (custom param flowed through)",
                w is not None and abs(w - 2.5) < 0.05, f"width={w}")
        else:
            add('Viewer HTML config pins style "tube"', False, "no viewer HTML in outputs")
            add("Viewer HTML config pins width 2.5 (custom param flowed through)",
                False, "no viewer HTML in outputs")

    json.dump(results, sys.stdout, indent=1)
    print()


if __name__ == "__main__":
    main()
