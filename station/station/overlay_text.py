"""English evidence labels with OpenCV's built-in Hershey font.

The Hershey fonts have no ç ğ ı İ ö ş ü glyphs, and putText draws them as
"?" or nothing. Each such letter is drawn as its ASCII base letter plus the
diacritic (cedilla, dots, breve, dot), so labels are spelt correctly without a
TrueType renderer or any new dependency.
"""
from functools import lru_cache
import cv2
import numpy as np

FONT = cv2.FONT_HERSHEY_SIMPLEX
# letter -> (base glyph, mark)
TURKISH = {"ç": ("c", "cedilla"), "Ç": ("C", "cedilla"), "ş": ("s", "cedilla"), "Ş": ("S", "cedilla"),
           "ö": ("o", "dots"), "Ö": ("O", "dots"), "ü": ("u", "dots"), "Ü": ("U", "dots"),
           "ğ": ("g", "breve"), "Ğ": ("G", "breve"), "İ": ("I", "dot"), "ı": ("ı", None)}


def _base(ch):
    return TURKISH.get(ch, (ch, None))[0]


@lru_cache(maxsize=256)
def _advance(ch, scale, thickness):
    # getTextSize pads every call by the stroke thickness; the pen advance is
    # the growth from one copy of the glyph to two.
    ch = "i" if ch == "ı" else ch
    return cv2.getTextSize(ch * 2, FONT, scale, thickness)[0][0] - cv2.getTextSize(ch, FONT, scale, thickness)[0][0]


def _display_text(text):
    # Localize the legacy annotation at the presentation boundary. The detector
    # and its confidence/box calculations remain unchanged.
    prefix = "Duman şüphesi %"
    if text.startswith(prefix):
        return "Smoke suspicion " + text[len(prefix):] + "%"
    return text


def text_size(text, scale, thickness):
    """Like cv2.getTextSize for the whole label, including marks above caps."""
    text = _display_text(text)
    width = sum(_advance(_base(ch), scale, thickness) for ch in text) + (cv2.getTextSize("a", FONT, scale, thickness)[0][0] - _advance("a", scale, thickness))
    (_, height), baseline = cv2.getTextSize("Hg", FONT, scale, thickness)
    if any(TURKISH.get(ch, (None, None))[1] in ("dots", "dot", "breve") and ch.isupper() for ch in text):
        height += round(-_ink("x", scale, thickness)[1] * .6)
    return (width, height), baseline


@lru_cache(maxsize=256)
def _ink(ch, scale, thickness):
    """Ink box of one glyph relative to its origin: (left, top, right), top < 0 above baseline."""
    (w, h), base = cv2.getTextSize(ch, FONT, scale, thickness)
    pad = 2 * thickness + 4
    canvas = np.zeros((h + base + 2 * pad, w + 2 * pad), np.uint8)
    origin = (pad, pad + h)
    cv2.putText(canvas, ch, origin, FONT, scale, 255, thickness, cv2.LINE_AA)
    ys, xs = np.nonzero(canvas > 96)
    if not len(xs):
        return 0, -h, w
    return int(xs.min()) - origin[0], int(ys.min()) - origin[1], int(xs.max()) - origin[0]


def put_text(image, text, org, scale, colour, thickness):
    text = _display_text(text)
    x, y = org
    x_top = _ink("x", scale, thickness)[1]          # negative: x-height above baseline
    radius = max(1, round(thickness * .9))
    gap = max(2, round(-x_top * .28))
    for ch in text:
        base, mark = TURKISH.get(ch, (ch, None))
        width = _advance(base, scale, thickness)
        if base == "ı":
            # Dotless i: the stem of "i" without its dot.
            left, _, right = _ink("i", scale, thickness)
            cx = x + (left + right) // 2
            cv2.line(image, (cx, y - thickness // 2), (cx, y + x_top + thickness // 2), colour, thickness, cv2.LINE_AA)
            x += width
            continue
        cv2.putText(image, base, (x, y), FONT, scale, colour, thickness, cv2.LINE_AA)
        if mark:
            left, top, right = _ink(base, scale, thickness)
            cx = x + (left + right) // 2
            above = y + top - gap - radius
            if mark == "dots":
                spread = max(radius + 1, round((right - left) * .22))
                for dx in (-spread, spread):
                    cv2.circle(image, (cx + dx, above), radius, colour, -1, cv2.LINE_AA)
            elif mark == "dot":
                cv2.circle(image, (cx, above), radius, colour, -1, cv2.LINE_AA)
            elif mark == "breve":
                half = max(2, round((right - left) * .28))
                cv2.ellipse(image, (cx, above - half // 2), (half, max(1, half // 2)), 0, 0, 180, colour, thickness, cv2.LINE_AA)
            elif mark == "cedilla":
                depth = max(3, round(-x_top * .4))
                hook = max(2, round((right - left) * .25))
                cv2.line(image, (cx, y), (cx, y + depth // 2), colour, thickness, cv2.LINE_AA)
                cv2.line(image, (cx, y + depth // 2), (cx - hook, y + depth), colour, thickness, cv2.LINE_AA)
        x += width
    return x
