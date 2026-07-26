"""Prep a photo for ASCII conversion.

Run once per photo, locally:

    python scripts/prep_photo.py Gati_Pic.jpg

Steps (per the reference pipeline):
  1. Optional crop to head and shoulders.
  2. Remove the background with rembg so only the subject remains.
  3. Boost local contrast with CLAHE on the subject only.
  4. Composite onto pure white so the background maps to the blank
     end of the ASCII ramp (white -> spaces).

Output: data/source-prepped.png (grayscale).
"""

import argparse
import sys

import cv2
import numpy as np
from PIL import Image
from rembg import remove


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("photo", help="source photo (jpg/png)")
    ap.add_argument("-o", "--out", default="data/source-prepped.png")
    ap.add_argument(
        "--crop",
        default=None,
        help="crop box as x,y,w,h in source pixels (default: full frame)",
    )
    ap.add_argument("--clahe-clip", type=float, default=2.5)
    args = ap.parse_args()

    img = Image.open(args.photo).convert("RGB")
    if args.crop:
        x, y, w, h = (int(v) for v in args.crop.split(","))
        img = img.crop((x, y, x + w, y + h))

    print("removing background (first run downloads the u2net model)...")
    cut = remove(img)  # RGBA, background transparent
    rgba = np.array(cut)
    alpha = rgba[:, :, 3].astype(np.float32) / 255.0

    gray = cv2.cvtColor(rgba[:, :, :3], cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=args.clahe_clip, tileGridSize=(8, 8))
    eq = clahe.apply(gray).astype(np.float32)

    # Composite the contrast-boosted subject onto pure white.
    out = eq * alpha + 255.0 * (1.0 - alpha)
    out = np.clip(out, 0, 255).astype(np.uint8)

    cv2.imwrite(args.out, out)
    print(f"wrote {args.out} ({out.shape[1]}x{out.shape[0]})")


if __name__ == "__main__":
    sys.exit(main())
