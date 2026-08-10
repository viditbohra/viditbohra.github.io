# igotyourmonkey.github.io

Personal site for Vidit Bohra. Plain HTML, CSS and JavaScript — no framework, no build
step, no dependencies. GitHub Pages serves it straight from the repo root.

## Editing

Text lives in `index.html`, styling in `style.css`, and the small amount of behaviour
(theme toggle, lightbox, video) in `script.js`. Colours are CSS custom properties defined
at the top of `style.css`; change them in one place and both themes follow.

To preview locally:

```
python -m http.server 8000
```

then open <http://localhost:8000>.

## Media

`assets/` is generated — don't edit it by hand. The originals live outside this repo in
`C:\Users\bohra\Desktop\website\` (the `biped`, `mrt`, `retargetting`,
`equivariance filter paper implementation`, `stress concentration` and `supprt free`
folders), and are deliberately not committed: 314 MB of HEIC photos and raw video that
browsers can't display anyway.

`tools/build_media.py` converts them into web-ready assets — HEIC to JPEG, .MOV/.webm to
MP4 with poster frames, EXIF rotation baked in, everything resized and compressed. To
regenerate after adding or swapping source files:

```
pip install pillow pillow-heif imageio-ffmpeg
python tools/build_media.py
```

Pass one or more project slugs to rebuild only part of the set, e.g.
`python tools/build_media.py mrt biped`.

The manifest at the top of that script maps each source filename to the output name used
in `index.html`, so renaming an asset means changing it in both places.
