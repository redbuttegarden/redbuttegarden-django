import re
from typing import Tuple

HEX_RE = re.compile(r"^#([0-9a-fA-F]{6})$")


def hex_to_rgb(hex_color: str) -> Tuple[float, float, float]:
    """
    Returns sRGB channels normalized to 0..1.
    """
    m = HEX_RE.match(hex_color.strip())
    if not m:
        raise ValueError(f"Invalid hex color: {hex_color}")
    h = m.group(1)
    r = int(h[0:2], 16) / 255.0
    g = int(h[2:4], 16) / 255.0
    b = int(h[4:6], 16) / 255.0
    return r, g, b


def srgb_to_linear(c: float) -> float:
    # WCAG definition
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(hex_color: str) -> float:
    r, g, b = hex_to_rgb(hex_color)
    rl = srgb_to_linear(r)
    gl = srgb_to_linear(g)
    bl = srgb_to_linear(b)
    return 0.2126 * rl + 0.7152 * gl + 0.0722 * bl


def contrast_ratio(fg_hex: str, bg_hex: str) -> float:
    L1 = relative_luminance(fg_hex)
    L2 = relative_luminance(bg_hex)
    lighter = max(L1, L2)
    darker = min(L1, L2)
    return (lighter + 0.05) / (darker + 0.05)
