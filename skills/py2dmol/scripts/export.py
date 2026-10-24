#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright", "imageio-ffmpeg"]
# ///
"""Export a py2Dmol viewer HTML page to a publication-ready image or video.

py2Dmol has no Python-side export: PNG/SVG/video are produced by the renderer's
JavaScript. This script opens the HTML in headless Chromium and drives that JS
API directly:

  - stills:  renderer.saveImage({format, dpi})      -> PNG (render scale) / SVG / SVGZ
  - videos:  renderer.startRecording()/stopRecording() -> WebM off the canvas

Exports always have a transparent background (by design — no baked-in white
rect). PNG `dpi` is a render scale: the picture is re-rendered at output size,
so 300 dpi on a 600 px view gives a genuinely finer 1875x1875 image. Recordings
are taken at canvas size; dpi does not apply. Convert with the bundled ffmpeg
when mp4/gif is requested (H.264 yuv420p + faststart for slide tools).

Drives an installed system Chrome/Edge when present (zero download); only
falls back to Playwright's own Chromium, auto-downloading it (~150 MB, once)
on machines with neither.

Usage:
    uv run scripts/export.py viewer.html -o fig.png [--dpi 300] [--viewer-id ID]
    uv run scripts/export.py viewer.html -o fig.svg
    uv run scripts/export.py viewer.html -o anim.mp4 [--seconds 10] [--speed 100]
    uv run scripts/export.py viewer.html -o anim.gif [--fps 15]
    uv run scripts/export.py viewer.html -o gallery.png --page [--scale 2]

`--page` captures the whole rendered page (all viewers, e.g. a grid, or a
structure + PAE-matrix pair) as a screenshot instead of a single-viewer
saveImage; `--scale` multiplies its resolution (the canvas is HiDPI-aware, so
this stays crisp). saveImage exports only the structure canvas, so PAE panels
always need --page.

Timing and scaling facts worth knowing:
  - Recording duration is frame-driven, not wall-clock: the renderer records
    nFrames x max(50, animationSpeed) ms and self-stops after the last frame
    (rotate recordings self-stop after one revolution). --seconds is only an
    upper bound on how long this script waits before forcing stopRecording.
    To get a longer/slower trajectory video, raise --speed (ms per frame), not
    --seconds: 40 frames x 200 ms = 8 s.
  - PNG dpi is a render scale re-rendered at output size, clamped by the
    renderer to [36, 1200]; 300 dpi on an 800 px view gives a ~2400 px image.
"""

import argparse
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

READY_JS = "() => window.py2dmol_viewers && Object.keys(window.py2dmol_viewers).length > 0"
SETTLE_SECONDS = 2.0  # fonts, layout, first animation frame


def fail(msg: str) -> None:
    print(f"export.py: error: {msg}", file=sys.stderr)
    sys.exit(1)


def png_dimensions(path: Path) -> tuple[int, int]:
    with open(path, "rb") as f:
        header = f.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        return (0, 0)
    w, h = struct.unpack(">II", header[16:24])
    return (w, h)


def launch_chromium(pw):
    """Prefer an installed system browser (zero download); fall back to
    Playwright's bundled Chromium, auto-installing it on first use."""
    for channel in ("chrome", "msedge"):
        try:
            return pw.chromium.launch(headless=True, channel=channel)
        except Exception:
            continue
    try:
        return pw.chromium.launch(headless=True)
    except Exception as e:
        if "playwright install" not in str(e) and "Executable doesn't exist" not in str(e):
            raise
        print("No system Chrome/Edge found — installing Playwright Chromium (~150 MB, one time)...", flush=True)
        proc = subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
        if proc.returncode != 0:
            fail("Chromium installation failed — run `playwright install chromium` manually")
        return pw.chromium.launch(headless=True)


def ffmpeg_exe() -> str:
    """Prefer a full system ffmpeg; fall back to the pip-bundled static build."""
    system = shutil.which("ffmpeg")
    if system:
        return system
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def convert_video(webm: Path, out: Path, fps: int) -> None:
    exe = ffmpeg_exe()
    if out.suffix == ".mp4":
        # yuv420p + faststart: plays everywhere (PowerPoint, Keynote, browsers).
        # pad to even dimensions first — libx264/yuv420p cannot encode odd
        # widths/heights, and py2Dmol canvases come out at internal render
        # scales that are frequently odd (e.g. 1047x1047).
        cmd = [exe, "-y", "-i", str(webm), "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
               "-c:v", "libx264", "-pix_fmt", "yuv420p",
               "-crf", "18", "-movflags", "+faststart", str(out)]
    elif out.suffix == ".gif":
        cmd = [exe, "-y", "-i", str(webm),
               "-vf", f"fps={fps},split[a][b];[a]palettegen=stats_mode=diff[p];"
                      f"[b][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle",
               "-loop", "0", str(out)]
    else:
        fail(f"unsupported video format {out.suffix!r} — use .mp4, .gif or .webm")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stderr[-2000:], file=sys.stderr)
        fail(f"ffmpeg conversion to {out.name} failed")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("html", help="viewer HTML produced by render.py")
    ap.add_argument("-o", "--out", required=True, help="output path: .png .svg .svgz .webm .mp4 .gif")
    ap.add_argument("--dpi", type=int, default=300, help="PNG render scale (default 300; ignored for svg/video)")
    ap.add_argument("--viewer-id", help="viewer to export when the page holds several (default: the only one)")
    ap.add_argument("--seconds", type=float, default=10.0, help="recording length before stopRecording (default 10)")
    ap.add_argument("--speed", type=int, help="ms per frame: sets renderer.animationSpeed before recording. "
                                              "Duration is frame-driven (nFrames x max(50, speed) ms, self-stopping), "
                                              "so raise this — not --seconds — for longer/slower trajectory videos")
    ap.add_argument("--fps", type=int, default=15, help="gif frame rate (default 15)")
    ap.add_argument("--page", action="store_true", help="screenshot the whole page (grids) instead of saveImage")
    ap.add_argument("--scale", type=int, default=2, help="device scale factor for --page screenshots (default 2)")
    ap.add_argument("--no-webm", action="store_true", help="delete the intermediate WebM after mp4/gif conversion")
    ap.add_argument("--wait", type=float, default=SETTLE_SECONDS, help="extra settle time after load (default 2s)")
    args = ap.parse_args()

    src = Path(args.html).resolve()
    if not src.is_file():
        fail(f"viewer HTML not found: {src}")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    ext = out.suffix.lower()
    is_video = ext in (".webm", ".mp4", ".gif")

    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = launch_chromium(pw)
        page = browser.new_page(viewport={"width": 1400, "height": 1000},
                                device_scale_factor=args.scale, accept_downloads=True)
        page.goto(src.as_uri())
        try:
            page.wait_for_function(READY_JS, timeout=30_000)
        except Exception:
            fail("no py2Dmol viewer appeared within 30s — the HTML may be broken or data failed to load")
        page.wait_for_timeout(int(args.wait * 1000))

        ids = page.evaluate("() => Object.keys(window.py2dmol_viewers)")

        if args.page:
            # Whole-page capture (grids): the canvas honours devicePixelRatio,
            # so device_scale_factor keeps it sharp. omit_background -> transparent.
            page.screenshot(path=str(out), full_page=True, omit_background=True)
            browser.close()
            done(out, extra=f"page mode, {len(ids)} viewer(s)")
            return

        vid = args.viewer_id or (ids[0] if len(ids) == 1 else None)
        if vid is None:
            fail(f"page holds several viewers ({ids}) — pass --viewer-id, or use --page to capture them all")

        if is_video:
            cfg = page.evaluate(f"() => window.py2dmol_configs && window.py2dmol_configs[{vid!r}] || {{}}")
            disp = cfg.get("display", cfg)  # rotate/autoplay live under config.display
            if not (disp.get("rotate") or disp.get("autoplay")):
                print(f"warning: viewer {vid} has neither rotate nor autoplay — "
                      "the recording will show a static structure", file=sys.stderr)
            webm_tmp = Path(tempfile.mkstemp(suffix=".webm")[1])
            if args.speed:
                page.evaluate("([id, s]) => { window.py2dmol_viewers[id].renderer.animationSpeed = s }", [vid, args.speed])
            with page.expect_download(timeout=int((args.seconds + 60) * 1000)) as dl:
                page.evaluate(f"id => window.py2dmol_viewers[id].renderer.startRecording()", vid)
                page.wait_for_timeout(int(args.seconds * 1000))
                # Rotate mode stops itself after one revolution; stopRecording is
                # the manual end for trajectory/Draw recordings.
                try:
                    page.evaluate(f"id => window.py2dmol_viewers[id].renderer.stopRecording()", vid)
                except Exception:
                    pass
            dl.value.save_as(str(webm_tmp))
            browser.close()
            if ext == ".webm":
                shutil.move(webm_tmp, out)
                done(out, extra="native recording")
            else:
                convert_video(webm_tmp, out, args.fps)
                keep = out.with_suffix(".webm")
                if args.no_webm:
                    webm_tmp.unlink()
                else:
                    shutil.move(webm_tmp, keep)
                    print(f"kept native recording as {keep}")
                done(out)
        else:
            fmt = {"png": "png", ".svg": "svg"}.get(ext.lstrip("."), ext.lstrip("."))
            if fmt not in ("png", "svg", "svgz"):
                fail(f"unsupported still format {ext!r} — use .png, .svg, .svgz, .mp4, .gif or .webm")
            opts = {"format": fmt}
            if fmt == "png":
                opts["dpi"] = args.dpi
            tmp = Path(tempfile.mkstemp(suffix=ext)[1])
            with page.expect_download(timeout=30_000) as dl:
                page.evaluate(f"([id, o]) => window.py2dmol_viewers[id].renderer.saveImage(o)", [vid, opts])
            dl.value.save_as(str(tmp))
            browser.close()
            shutil.move(tmp, out)
            if fmt == "png":
                w, h = png_dimensions(out)
                done(out, extra=f"{w}x{h}")
            else:
                done(out)


def done(out: Path, extra: str = "") -> None:
    size = out.stat().st_size if out.exists() else 0
    note = f" ({extra})" if extra else ""
    print(f"wrote {out}{note} — {size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
