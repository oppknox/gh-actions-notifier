"""Pillow-generated tray status icons.

Each icon is a 64x64 RGBA circle with a small highlight, generated at
runtime so no image files need to be shipped with the package.
"""

from PIL import Image, ImageDraw

SIZE = 64
COLORS = {
    "ok": "#2ea44f",       # green
    "error": "#d73a49",    # red
    "disconnected": "#f0883e",  # orange
    "polling": "#0969da",  # blue
}


def _make_icon(color: str) -> Image.Image:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    margin = 4
    draw.ellipse(
        [margin, margin, SIZE - margin, SIZE - margin],
        fill=color,
    )
    # Inner highlight
    inner = SIZE // 4
    draw.ellipse(
        [inner, inner, inner + SIZE // 6, inner + SIZE // 6],
        fill="#ffffff80",
    )
    return img


def icon_ok() -> Image.Image:
    return _make_icon(COLORS["ok"])


def icon_error() -> Image.Image:
    return _make_icon(COLORS["error"])


def icon_disconnected() -> Image.Image:
    return _make_icon(COLORS["disconnected"])


def icon_polling() -> Image.Image:
    return _make_icon(COLORS["polling"])
