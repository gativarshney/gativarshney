"""Convert the prepped photo into a self-typing monochrome ASCII SVG.

Run once, locally, after prep_photo.py:

    python scripts/make_ascii_svg.py            # writes gati-ascii.svg
    python scripts/make_ascii_svg.py --preview  # also prints the grid to stdout
    STATIC=1 python scripts/make_ascii_svg.py   # frozen frame, no animation

Design rules (per the reference pipeline):
  - Monochrome: one light-gray fill. No per-character coloring.
  - The ramp starts with a space so the white background prints as nothing.
  - Each row wipes in left-to-right (SMIL clip animation), staggered top to
    bottom. Plays once and freezes; a block cursor blinks briefly, then stops.
"""

import argparse
import os
import sys
from html import escape

import cv2
import numpy as np

RAMP = " .`:-=+*cs#%@"  # bright (sparse) -> dark (dense)

# Palette (shared across all profile SVGs)
BG = "#0d1117"
BORDER = "#30363d"
INK = "#c9d1d9"
ACCENT = "#3fb950"

FONT = "ui-monospace, SFMono-Regular, 'Cascadia Mono', Menlo, Consolas, monospace"
FS = 10.0          # font size px
LH = 10.0          # line height px
CW = FS * 0.60     # monospace advance width px
CHAR_ASPECT = CW / LH

WIPE_DUR = 0.45    # seconds per row wipe
STAGGER = 0.07     # seconds between row starts
PAD = 16.0


def to_grid(img: np.ndarray, cols: int, gamma: float) -> list[str]:
    h, w = img.shape
    rows = max(1, round(cols * (h / w) * CHAR_ASPECT))
    small = cv2.resize(img, (cols, rows), interpolation=cv2.INTER_AREA).astype(np.float32)

    # Auto-levels over the subject only: stretch the subject's tonal range
    # across the whole ramp so the face gets dense glyphs instead of
    # washing out. Background (near-white) stays white -> spaces.
    subject = small[small < 245.0]
    if subject.size:
        lo = float(np.percentile(subject, 2))
        hi = float(np.percentile(subject, 90))
        stretched = (small - lo) / max(hi - lo, 1e-6) * 255.0
        small = np.where(small >= 245.0, 255.0, np.clip(stretched, 0, 255))

    norm = (small / 255.0) ** gamma
    idx = np.rint((1.0 - norm) * (len(RAMP) - 1)).astype(int)
    return ["".join(RAMP[i] for i in row) for row in idx]


def build_svg(grid: list[str], static: bool) -> str:
    rows = len(grid)
    cols = len(grid[0])
    text_w = cols * CW
    width = text_w + 2 * PAD
    height = rows * LH + 2 * PAD

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" '
        f'height="{height:.0f}" viewBox="0 0 {width:.0f} {height:.0f}">',
        f'<rect width="100%" height="100%" rx="8" fill="{BG}" '
        f'stroke="{BORDER}" stroke-width="1"/>',
        "<defs>",
    ]

    if not static:
        for i in range(rows):
            begin = i * STAGGER
            parts.append(
                f'<clipPath id="r{i}">'
                f'<rect x="{PAD:.1f}" y="{PAD + i * LH:.1f}" width="0" height="{LH:.1f}">'
                f'<animate attributeName="width" from="0" to="{text_w:.1f}" '
                f'begin="{begin:.2f}s" dur="{WIPE_DUR}s" fill="freeze"/>'
                f"</rect></clipPath>"
            )
    parts.append("</defs>")

    parts.append(
        f'<g font-family="{FONT}" font-size="{FS}" font-weight="bold" fill="{INK}">'
    )
    for i, line in enumerate(grid):
        clip = "" if static else f' clip-path="url(#r{i})"'
        y = PAD + i * LH + FS * 0.8
        # Browsers collapse regular spaces in SVG text (xml:space is ignored
        # by Chromium), which breaks column alignment. Non-breaking spaces
        # are never collapsed, so every row keeps exactly `cols` glyphs.
        row = escape(line).replace(" ", " ")
        parts.append(
            f'<text x="{PAD:.1f}" y="{y:.1f}" textLength="{text_w:.1f}" '
            f'lengthAdjust="spacing"{clip}>{row}</text>'
        )
    parts.append("</g>")

    if not static:
        # Block cursor: appears when the last row finishes, blinks, then stops.
        done = rows * STAGGER + WIPE_DUR
        cx = PAD + text_w - CW
        cy = PAD + (rows - 1) * LH + 1
        parts.append(
            f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{CW:.1f}" height="{LH - 2:.1f}" '
            f'fill="{ACCENT}" opacity="0">'
            f'<animate attributeName="opacity" values="0;1;0;1;0;1;0" '
            f'begin="{done:.2f}s" dur="2.4s" fill="freeze"/>'
            f"</rect>"
        )

    parts.append("</svg>")
    return "\n".join(parts)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", default="data/source-prepped.png")
    ap.add_argument("--out", default="gati-ascii.svg")
    ap.add_argument("--cols", type=int, default=100)
    ap.add_argument("--gamma", type=float, default=2.1,
                    help=">1 darkens midtones (denser glyphs)")
    ap.add_argument("--preview", action="store_true",
                    help="print the character grid to stdout")
    args = ap.parse_args()

    img = cv2.imread(args.src, cv2.IMREAD_GRAYSCALE)
    if img is None:
        sys.exit(f"cannot read {args.src}; run scripts/prep_photo.py first")

    grid = to_grid(img, args.cols, args.gamma)
    if args.preview:
        print("\n".join(grid))

    static = os.environ.get("STATIC") == "1"
    svg = build_svg(grid, static)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {args.out} ({len(grid[0])}x{len(grid)} chars, "
          f"{'static' if static else 'animated'})")


if __name__ == "__main__":
    main()
