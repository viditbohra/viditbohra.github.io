"""Convert the raw project media into web-ready assets.

Reads from the folders on the Desktop, writes into site/assets/. Source files are
never modified. Run from anywhere:  python tools/build_media.py

Handles the three things browsers can't take as-is: HEIC photos, .MOV/.webm video,
and EXIF-rotated JPEGs that would otherwise display sideways.
"""

import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import imageio_ffmpeg
import pillow_heif
from PIL import Image, ImageEnhance, ImageOps

pillow_heif.register_heif_opener()

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
SRC = Path(r"C:\Users\bohra\Desktop\website")
OUT = Path(__file__).resolve().parent.parent / "assets"

FULL_EDGE = 1600
THUMB_EDGE = 800
VIDEO_HEIGHT = 720
VIDEO_CRF = 30
VIDEO_MAX_SECONDS = 12

# Each entry maps a source filename to the output name used in index.html.
# Videos may carry (start_seconds, duration_seconds) to trim dead air.
MANIFEST = {
    "retargeting": {
        "src": "retargetting",
        "images": {
            "Screenshot 2026-08-10 170156.png": "point-cloud",
        },
        "videos": {
            "Screencast from 07-16-2026 08_40_17 AM (1).webm": ("object-scan", 0, None),
            "resconstruct_test1.mp4": ("source-video", 0, None),
            "test2_mesh_test (1).mp4": ("smpl-body", 0, None),
            "Screencast from 07-16-2026 11_07_24 AM (1).webm": ("object-mesh", 0, None),
            "Screencast from 07-01-2026 09_28_09 AM (1).webm": ("pepper-sim", 2, 12),
            "Screencast from 06-25-2026 11_21_17 AM.webm": ("humanoid-sim", 2, 12),
        },
    },
    "mrt": {
        "src": "mrt",
        "images": {
            "896348AA-302C-43DF-8A2B-08343EDB0DE3.JPG": "bevel-drive",
            "25A9E5E5-93CA-4ABD-91D1-D5422BB55E9E.JPG": "rail-cad",
            "6BFC0264-A6DF-4B09-AC07-1E774D9EF7D7.JPG": "cycloidal-assembly",
            "c7902eb2-73fb-4242-b5d9-7d0866842fff.JPG": "rover-cad",
            "IMG_2757.HEIC": "cycloidal-drive",
            "IMG_3245.HEIC": "differential-wrist",
            "IMG_3336.HEIC": "linear-base",
            "IMG_3774.HEIC": "rover-field",
        },
        "videos": {
            "IMG_2851.MOV": ("linear-base-demo", 0, None),
            "IMG_3948.MOV": ("wrist-motor", 0, None),
            "Screen Recording 2025-10-07 134343.mp4": ("linear-base-cad", 0, None),
            "Screen Recording 2025-10-07 133909.mp4": ("gearbox-cad", 0, None),
        },
    },
    "biped": {
        "src": "biped",
        "zip": "drive-download-20260810T113029Z-1-001.zip",
        "images": {
            "IMG_2663.PNG": "cad-render",
            "1F3222A2-CFE5-4EB1-9B30-0B3630C7CEBA.JPG": "cad-assembly",
            "IMG_2642.HEIC": "hardware",
            "Copy of Screenshot 2026-03-12 002903.png": "simulink-model",
        },
        "videos": {
            "Copy of Screen Recording 2026-03-12 003123.mp4": ("rl-policy", 0, 12),
            "Copy of IMG_2625.MOV": ("walking", 0, 12),
            "Copy of IMG_2628.MOV": ("balance-test", 0, 12),
            "Copy of 1FDEAA22-C683-4F28-80E6-9BB075416F7F.MP4": ("gait-sim", 0, 12),
            "Copy of D32731C9-D5DC-4748-B9F9-50868ACF700C.MP4": ("assembly", 0, 12),
        },
    },
    "equivariant-filter": {
        "src": "equivariance filter paper implementation",
        "images": {
            "trajectory_plot.png": "trajectory",
            "allan_deviation.png": "allan-deviation",
            "Screenshot 2026-08-10 173313.png": "landmark-map",
            "WhatsApp Image 2026-08-10 at 5.18.51 PM.jpeg": "camera-imu-rig",
            "WhatsApp Image 2026-08-10 at 5.18.58 PM.jpeg": "rig-detail",
        },
        "videos": {
            "Screen Recording 2026-08-10 173036.mp4": ("vio-run", 10, 12),
        },
    },
    "support-free": {
        "src": "supprt free",
        "images": {
            "Screenshot 2026-05-02 172032.png": "cad-model",
            "Screenshot 2026-05-04 145928.png": "printed-part",
            "Screenshot 2026-04-18 171445.png": "nozzle-angle",
            "Screenshot 2026-04-18 174834.png": "conical-part",
            "Screenshot 2026-05-04 145222.png": "overhang-part",
            "Screenshot 2026-05-04 145613.png": "overhang-detail",
        },
        "videos": {
            "WhatsApp Video 2026-08-10 at 5.16.28 PM.mp4": ("printing", 0, 11),
            "WhatsApp Video 2026-08-10 at 5.16.26 PM.mp4": ("print-run", 5, 12),
            "WhatsApp Video 2026-08-10 at 5.16.27 PM.mp4": ("nozzle-path", 3, 12),
        },
    },
    "stress-concentration": {
        "src": "stress concentration",
        # Shot through a polariscope: a small lit disc on a mostly black frame.
        # Crop away the dead border, then lift the exposure so the fringes read.
        "autocrop": True,
        "brighten": 1.35,
        "images": {
            "IMG_4320.jpg": "square-hole",
            "IMG_4319.jpg": "square-hole-detail",
            "IMG_4318.jpg": "filleted-hole",
            "IMG_4267.HEIC": "elliptical-hole",
            "IMG_4269.HEIC": "elliptical-hole-detail",
            "IMG_4288.jpg": "square-hole-wide",
        },
    },
}


def autocrop_dark_border(im: Image.Image, threshold: int = 70) -> Image.Image:
    """Trim a near-black surround down to the lit subject, with a little breathing room."""
    mask = im.convert("L").point(lambda v: 255 if v > threshold else 0)
    box = mask.getbbox()
    if not box:
        return im
    left, top, right, bottom = box
    pad_x = int((right - left) * 0.04)
    pad_y = int((bottom - top) * 0.04)
    return im.crop((
        max(0, left - pad_x),
        max(0, top - pad_y),
        min(im.width, right + pad_x),
        min(im.height, bottom + pad_y),
    ))


def convert_image(
    src: Path,
    dest_stem: Path,
    brighten: float | None = None,
    autocrop: bool = False,
) -> None:
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)  # bake in rotation, don't trust the viewer
        if im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
        if autocrop:
            im = autocrop_dark_border(im)
        if brighten:
            im = ImageEnhance.Brightness(im).enhance(brighten)
            im = ImageEnhance.Contrast(im).enhance(1.1)

        for edge, quality, suffix in (
            (FULL_EDGE, 82, ".jpg"),
            (THUMB_EDGE, 78, "-thumb.jpg"),
        ):
            copy = im.copy()
            copy.thumbnail((edge, edge), Image.LANCZOS)
            copy.save(
                dest_stem.with_name(dest_stem.name + suffix),
                "JPEG",
                quality=quality,
                optimize=True,
                progressive=True,
            )


def convert_video(src: Path, dest_stem: Path, start: float, duration: float | None) -> None:
    mp4 = dest_stem.with_suffix(".mp4")
    cmd = [FFMPEG, "-y", "-loglevel", "error"]
    if start:
        cmd += ["-ss", str(start)]
    cmd += ["-i", str(src)]
    cmd += ["-t", str(duration if duration else VIDEO_MAX_SECONDS)]
    cmd += [
        "-an",  # every one of these is silent or has useless audio
        "-c:v", "libx264",
        "-profile:v", "main",
        "-pix_fmt", "yuv420p",
        "-crf", str(VIDEO_CRF),
        "-preset", "slow",
        # scale to at most VIDEO_HEIGHT tall, keep aspect, force even dimensions
        "-vf", f"scale=-2:'min({VIDEO_HEIGHT},ih)':flags=lanczos",
        "-movflags", "+faststart",
        str(mp4),
    ]
    subprocess.run(cmd, check=True, capture_output=True)

    # Poster frame, so the page shows a still until someone clicks play.
    poster = dest_stem.with_name(dest_stem.name + "-poster.jpg")
    subprocess.run(
        [FFMPEG, "-y", "-loglevel", "error", "-i", str(mp4),
         "-frames:v", "1", "-q:v", "4", str(poster)],
        check=True, capture_output=True,
    )


def main() -> int:
    # Optional project slugs to rebuild just part of the set while iterating.
    only = set(sys.argv[1:])
    if not only and OUT.exists():
        shutil.rmtree(OUT)

    failures = []
    for slug, cfg in MANIFEST.items():
        if only and slug not in only:
            continue
        dest_dir = OUT / slug
        dest_dir.mkdir(parents=True, exist_ok=True)
        src_dir = SRC / cfg["src"]
        search_dirs = [src_dir]
        tmp = None

        if "zip" in cfg:
            tmp = Path(tempfile.mkdtemp(prefix="media-"))
            with zipfile.ZipFile(src_dir / cfg["zip"]) as zf:
                zf.extractall(tmp)
            search_dirs.append(tmp)

        def locate(name: str) -> Path | None:
            for d in search_dirs:
                hit = d / name
                if hit.exists():
                    return hit
            return None

        try:
            print(f"\n{slug}")
            for name, out_name in cfg.get("images", {}).items():
                path = locate(name)
                if path is None:
                    failures.append(f"{slug}: missing image {name}")
                    continue
                try:
                    convert_image(
                        path,
                        dest_dir / out_name,
                        cfg.get("brighten"),
                        cfg.get("autocrop", False),
                    )
                    print(f"  img  {out_name}")
                except Exception as exc:
                    failures.append(f"{slug}/{name}: {exc}")

            for name, (out_name, start, dur) in cfg.get("videos", {}).items():
                path = locate(name)
                if path is None:
                    failures.append(f"{slug}: missing video {name}")
                    continue
                try:
                    convert_video(path, dest_dir / out_name, start, dur)
                    print(f"  vid  {out_name}")
                except Exception as exc:
                    failures.append(f"{slug}/{name}: {exc}")
        finally:
            if tmp:
                shutil.rmtree(tmp, ignore_errors=True)

    files = list(OUT.rglob("*.*"))
    total = sum(f.stat().st_size for f in files)
    biggest = max(files, key=lambda f: f.stat().st_size)
    print(f"\n{len(files)} files, {total / 1024 / 1024:.1f} MB total")
    print(f"largest: {biggest.relative_to(OUT)} at {biggest.stat().st_size / 1024 / 1024:.1f} MB")

    if failures:
        print(f"\n{len(failures)} problem(s):")
        for f in failures:
            print(f"  {f}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
