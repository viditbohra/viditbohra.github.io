"""Convert the raw project media into web ready assets.

Reads from the folders on the Desktop, writes into site/assets/. Source files are
never modified. Run from anywhere:  python tools/build_media.py

Pass project slugs to rebuild only part of the set, e.g.
    python tools/build_media.py mars-rover-arm bipedal-robot

Handles the three things browsers cannot take as is: HEIC photos, MOV and WebM
video, and EXIF rotated JPEGs that would otherwise display sideways. It also
writes assets/dimensions.json, which build_site.py uses to lay galleries out at
each image's true shape.
"""

import json
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
SRC = Path(__file__).resolve().parent.parent.parent
OUT = Path(__file__).resolve().parent.parent / "assets"

FULL_EDGE = 1600
THUMB_EDGE = 800
VIDEO_HEIGHT = 720
VIDEO_CRF = 30
VIDEO_MAX_SECONDS = 12

# Maps each source filename to the output name used by build_site.py.
# Videos carry (name, start_seconds, duration_seconds) to trim dead air.
MANIFEST = {
    "me": {
        "src": "me",
        # Square crop centred on the face, so the circular frame on the page
        # lands on a head and shoulders shot rather than the whole photo.
        "face_crop": True,
        "images": {
            "IMG_0254.jpg": "portrait",
        },
    },
    "retargeting": {
        "src": "retargetting",
        "images": {
            "Screenshot 2026-08-10 170156.png": "point-cloud",
        },
        "videos": {
            "Screencast from 07-01-2026 09_28_09 AM (1).webm": ("pepper-sim", 2, 12),
            "Screencast from 06-26-2026 01_28_43 PM (1).webm": ("pepper-arms", 2, 12),
            "Screencast from 07-01-2026 11_03_19 AM (1).webm": ("ur5-arm", 2, 12),
            "Screencast from 06-25-2026 11_21_17 AM.webm": ("humanoid-sim", 2, 12),
            "test2_mesh_test (1).mp4": ("smpl-body", 0, None),
        },
    },
    "mars-rover-arm": {
        "src": "mrt",
        "images": {
            "IMG_3774.HEIC": "rover-field",
            "Screenshot 2026-02-25 202137.png": "arm-cad",
            "c7902eb2-73fb-4242-b5d9-7d0866842fff.JPG": "rover-cad",
            "IMG_3336.HEIC": "cycloidal-drive",
            "6BFC0264-A6DF-4B09-AC07-1E774D9EF7D7.JPG": "wrist-assembly",
            "IMG_3245.HEIC": "wrist-build",
        },
        "videos": {
            "Screen Recording 2025-10-07 133909.mp4": ("wrist-cad", 0, None),
            "Screen Recording 2025-10-07 134343.mp4": ("linear-base-cad", 0, None),
            "IMG_2851.MOV": ("linear-base-demo", 0, None),
        },
    },
    "bipedal-robot": {
        "src": "biped",
        "zip": "drive-download-20260810T113029Z-1-001.zip",
        "images": {
            "IMG_2663.PNG": "cad-render",
            "IMG_2642.HEIC": "hardware",
            "Copy of Screenshot 2026-03-12 002903.png": "simscape-model",
            "IMG_6675.HEIC": "leg-test-rig",
        },
        "videos": {
            "Copy of 1FDEAA22-C683-4F28-80E6-9BB075416F7F.MP4": ("rl-policy", 0, 12),
            "Copy of Screen Recording 2026-03-12 003123.mp4": ("data-driven-control", 0, 12),
            "Copy of IMG_2628.MOV": ("hardware-test", 0, 12),
        },
    },
    "state-estimation": {
        "src": "equivariance filter paper implementation",
        "images": {
            "WhatsApp Image 2026-08-10 at 5.18.51 PM.jpeg": "camera-imu-rig",
            "WhatsApp Image 2026-08-10 at 5.18.58 PM.jpeg": "rig-detail",
            "trajectory_plot.png": "trajectory",
            "Screenshot 2026-08-10 173313.png": "landmark-map",
            "allan_deviation.png": "allan-deviation",
        },
        "videos": {
            # The first 20 seconds are the camera pointed at a blank ceiling, with
            # almost nothing to track. Skipping them starts the clip on the desk
            # scene and runs to the end of the recording, which is where the
            # filter is actually doing visible work.
            "Screen Recording 2026-08-10 173036.mp4": ("vio-run", 20, 70),
        },
    },
    "support-free-printing": {
        "src": "supprt free",
        "images": {
            "Screenshot 2026-05-04 145928.png": "printed-part",
            "Screenshot 2026-05-02 172032.png": "cad-model",
            "Screenshot 2026-04-18 171445.png": "nozzle-angle",
        },
        "videos": {
            "WhatsApp Video 2026-08-10 at 5.16.27 PM.mp4": ("nozzle-path", 3, 12),
        },
    },
    "photoelasticity": {
        "src": "stress concentration",
        # Shot through a polariscope: a small lit disc on a mostly black frame.
        # Crop away the dead border, then lift the exposure so the fringes read.
        "autocrop": True,
        "brighten": 1.35,
        "images": {
            "IMG_4320.jpg": "square-hole",
            "IMG_4318.jpg": "filleted-hole",
            "IMG_4267.HEIC": "elliptical-hole",
            "IMG_4319.jpg": "square-hole-detail",
            "IMG_4269.HEIC": "elliptical-hole-detail",
            "IMG_4288.jpg": "square-hole-wide",
        },
    },
}


def autocrop_dark_border(im: Image.Image, threshold: int = 70) -> Image.Image:
    """Trim a near black surround down to the lit subject, with a little breathing room."""
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


def square_on_face(im: Image.Image) -> Image.Image:
    """Square crop framing the face: head with a little air above, shoulders below.

    Falls back to an upper centre crop, which is where a face sits in a portrait
    anyway, if the detector finds nothing.
    """
    import cv2
    import numpy as np

    grey = cv2.cvtColor(np.array(im.convert("RGB")), cv2.COLOR_RGB2GRAY)
    cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    faces = cascade.detectMultiScale(grey, scaleFactor=1.1, minNeighbors=6,
                                     minSize=(int(im.width * 0.06),) * 2)

    if len(faces):
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        side = min(int(w * 2.6), im.width, im.height)
        cx = x + w / 2
        cy = y + h / 2 + h * 0.32  # drop the centre so the chin is not on the edge
    else:
        side = min(im.width, im.height)
        cx, cy = im.width / 2, side / 2

    left = int(max(0, min(cx - side / 2, im.width - side)))
    top = int(max(0, min(cy - side / 2, im.height - side)))
    return im.crop((left, top, left + side, top + side))


def convert_image(src, dest_stem, brighten=None, autocrop=False, face_crop=False):
    """Returns the (width, height) of the displayed thumbnail."""
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)  # bake in rotation, do not trust the viewer
        if im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
        if autocrop:
            im = autocrop_dark_border(im)
        if face_crop:
            im = square_on_face(im)
        if brighten:
            im = ImageEnhance.Brightness(im).enhance(brighten)
            im = ImageEnhance.Contrast(im).enhance(1.1)

        size = None
        for edge, quality, suffix in ((FULL_EDGE, 82, ".jpg"), (THUMB_EDGE, 78, "-thumb.jpg")):
            copy = im.copy()
            copy.thumbnail((edge, edge), Image.LANCZOS)
            copy.save(
                dest_stem.with_name(dest_stem.name + suffix),
                "JPEG", quality=quality, optimize=True, progressive=True,
            )
            size = copy.size
        return size


def convert_video(src, dest_stem, start, duration):
    """Returns the (width, height) of the generated poster frame."""
    mp4 = dest_stem.with_suffix(".mp4")
    cmd = [FFMPEG, "-y", "-loglevel", "error"]
    if start:
        cmd += ["-ss", str(start)]
    cmd += ["-i", str(src), "-t", str(duration if duration else VIDEO_MAX_SECONDS)]
    cmd += [
        "-an",  # every one of these is silent or has useless audio
        "-c:v", "libx264", "-profile:v", "main", "-pix_fmt", "yuv420p",
        "-crf", str(VIDEO_CRF), "-preset", "slow",
        "-vf", f"scale=-2:'min({VIDEO_HEIGHT},ih)':flags=lanczos",
        "-movflags", "+faststart",
        str(mp4),
    ]
    subprocess.run(cmd, check=True, capture_output=True)

    # Poster frame, so galleries show a still until someone clicks play.
    poster = dest_stem.with_name(dest_stem.name + "-poster.jpg")
    subprocess.run(
        [FFMPEG, "-y", "-loglevel", "error", "-i", str(mp4),
         "-frames:v", "1", "-q:v", "4", str(poster)],
        check=True, capture_output=True,
    )
    with Image.open(poster) as im:
        return im.size


def main():
    only = set(sys.argv[1:])
    dims_file = OUT / "dimensions.json"
    dims = {}
    if only and dims_file.exists():
        dims = json.loads(dims_file.read_text())
    elif not only and OUT.exists():
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

        if "zip" in cfg and (src_dir / cfg["zip"]).exists():
            tmp = Path(tempfile.mkdtemp(prefix="media-"))
            with zipfile.ZipFile(src_dir / cfg["zip"]) as zf:
                zf.extractall(tmp)
            search_dirs.append(tmp)

        def locate(name):
            for d in search_dirs:
                if (d / name).exists():
                    return d / name
            return None

        try:
            print(f"\n{slug}")
            for name, out_name in cfg.get("images", {}).items():
                path = locate(name)
                if path is None:
                    failures.append(f"{slug}: source image missing, {name}")
                    continue
                try:
                    w, h = convert_image(path, dest_dir / out_name,
                                         cfg.get("brighten"), cfg.get("autocrop", False),
                                         cfg.get("face_crop", False))
                    dims[f"{slug}/{out_name}"] = [w, h]
                    print(f"  img  {out_name}  {w}x{h}")
                except Exception as exc:
                    failures.append(f"{slug}/{name}: {exc}")

            for name, (out_name, start, dur) in cfg.get("videos", {}).items():
                path = locate(name)
                if path is None:
                    failures.append(f"{slug}: source video missing, {name}")
                    continue
                try:
                    w, h = convert_video(path, dest_dir / out_name, start, dur)
                    dims[f"{slug}/{out_name}"] = [w, h]
                    print(f"  vid  {out_name}  {w}x{h}")
                except Exception as exc:
                    failures.append(f"{slug}/{name}: {exc}")
        finally:
            if tmp:
                shutil.rmtree(tmp, ignore_errors=True)

    dims_file.write_text(json.dumps(dict(sorted(dims.items())), indent=1))

    files = [f for f in OUT.rglob("*.*") if f.suffix != ".json"]
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
