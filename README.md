# viditbohra.github.io

Personal site for Vidit Bohra. Plain HTML, CSS and JavaScript. No framework and no
dependencies at runtime. GitHub Pages serves it straight from the repo root.

A landing page introduces me and lists the projects as cards. Each card opens its own
page with the writeup, photos and video.

## Editing the words

**All the text lives in `tools/build_site.py`**, near the top. The HTML files are
generated from it, so edit that file and re-run:

```
python tools/build_site.py
```

That rewrites `index.html` and everything in `projects/`. Editing those HTML files
directly works, but the next run will overwrite them, so change the Python instead.

The script also fails if an en dash or em dash ends up anywhere in the output, since
this site uses plain hyphens.

Styling is in `style.css`. Colours are CSS custom properties at the top of that file;
change them in one place and both the light and dark themes follow. The small amount of
behaviour, theme toggle, lightbox and click to play video, is in `script.js`.

To preview locally:

```
python -m http.server 8000
```

then open <http://localhost:8000>.

## Media

`assets/` is generated. Do not edit it by hand.

The originals live outside this repo in `C:\Users\bohra\Desktop\website\`, in the `me`,
`biped`, `mrt`, `retargetting`, `equivariance filter paper implementation`,
`stress concentration` and `supprt free` folders. They are deliberately not committed:
hundreds of MB of HEIC photos and raw video that browsers cannot display anyway.

Deleting a source file is fine. Drop it from the manifest in `build_media.py` and from
the matching `gallery` list in `build_site.py`, then run both. `build_site.py` refuses to
build if a page still references media that was not produced.

`tools/build_media.py` converts them into web ready assets. It decodes HEIC to JPEG,
transcodes MOV and WebM to MP4 with a poster frame, bakes in EXIF rotation so photos are
not sideways, resizes and compresses everything, and crops the dark border off the
polariscope shots. The result is about 14 MB.

To regenerate after adding or swapping source files:

```
pip install pillow pillow-heif imageio-ffmpeg
python tools/build_media.py
```

Pass one or more project slugs to rebuild only part of the set, for example
`python tools/build_media.py mars-rover-arm bipedal-robot`.

Both scripts use the same six slugs, so a project's folder name in `assets/`, its page
filename in `projects/`, and its key in each script all match:

`retargeting`, `mars-rover-arm`, `bipedal-robot`, `state-estimation`,
`support-free-printing`, `photoelasticity`

Adding a new photo or clip means adding it to the manifest in `build_media.py` and to
the matching project's `gallery` list in `build_site.py`, then running both scripts.
