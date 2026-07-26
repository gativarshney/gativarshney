"""Generate self-hosted terminal-style link badges.

Small pill SVGs in the shared palette, one per external link. The README
wraps each in an <a>, so nothing depends on shields.io or any hosted
badge service. Rerun whenever the badge list changes:

    python scripts/make_badges.py   # writes badges/*.svg
"""

import os
from html import escape

BG = "#0d1117"
BORDER = "#30363d"
INK = "#c9d1d9"
ACCENT = "#3fb950"

FONT = "ui-monospace, SFMono-Regular, 'Cascadia Mono', Menlo, Consolas, monospace"
FS = 15.0
CW = FS * 0.602
H = 38

# (filename, label)
BADGES = [
    ("gsoc", "gsoc '26"),
    ("openprinting", "openprinting commits"),
    ("hall-of-fame", "hall of fame"),
    ("woc", "woc 5.0 top 20"),
    ("linkedin", "linkedin"),
    ("leetcode", "leetcode"),
    ("email", "email"),
    ("interview-copilot", "interview-copilot"),
    ("ic-live", "live demo"),
    ("mystery-message", "mystery-message"),
    ("mm-live", "live demo"),
]


def main() -> None:
    os.makedirs("badges", exist_ok=True)
    for name, label in BADGES:
        text = escape(label)
        w = round(38 + len(label) * CW + 18)
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" '
            f'height="{H}" viewBox="0 0 {w} {H}">'
            f'<rect x="0.5" y="0.5" width="{w - 1}" height="{H - 1}" rx="8" '
            f'fill="{BG}" stroke="{BORDER}"/>'
            f'<text x="15" y="25" font-family="{FONT}" font-size="{FS}" '
            f'font-weight="bold" fill="{ACCENT}">&#10095;</text>'
            f'<text x="32" y="25" font-family="{FONT}" font-size="{FS}" '
            f'fill="{INK}">{text}</text>'
            f"</svg>"
        )
        path = f"badges/{name}.svg"
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"wrote {path} ({w}x{H})")


if __name__ == "__main__":
    main()
