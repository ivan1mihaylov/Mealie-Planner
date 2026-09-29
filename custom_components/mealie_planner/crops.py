"""Product pictures cut out of brochure pages.

When AI reads a brochure page it also says where each product's picture is
on it, as a box in fractions of the page. That part of the page, already
downloaded for the AI, is cut out and kept as a small JPEG, served by Home
Assistant like any static file.
"""

from __future__ import annotations

from io import BytesIO
import logging
from typing import Any

_LOGGER = logging.getLogger(__name__)

# Room around the box: a picture drawn right up to its edge still looks whole.
_MARGIN = 0.01
_SIZE = 480


def clean_box(box: Any) -> tuple[float, float, float, float] | None:
    """A box as (left, top, right, bottom) fractions, or None when it makes no sense."""
    if not isinstance(box, (list, tuple)) or len(box) != 4:
        return None
    try:
        left, top, right, bottom = (float(value) for value in box)
    except (TypeError, ValueError):
        return None
    # Some models answer in percent.
    if max(left, top, right, bottom) > 1.5:
        left, top, right, bottom = (value / 100 for value in (left, top, right, bottom))
    left, top = max(0.0, left), max(0.0, top)
    right, bottom = min(1.0, right), min(1.0, bottom)
    if right - left < 0.03 or bottom - top < 0.03:
        return None
    return left, top, right, bottom


def crop(data: bytes, box: tuple[float, float, float, float]) -> bytes | None:
    """The boxed part of a page image, as a JPEG no larger than 480 px; None without Pillow."""
    try:
        from PIL import Image
    except ImportError:  # pragma: no cover - Home Assistant ships with Pillow
        return None
    try:
        with Image.open(BytesIO(data)) as page:
            width, height = page.size
            left, top, right, bottom = box
            area = (
                int(max(0.0, left - _MARGIN) * width),
                int(max(0.0, top - _MARGIN) * height),
                int(min(1.0, right + _MARGIN) * width),
                int(min(1.0, bottom + _MARGIN) * height),
            )
            picture = page.crop(area).convert("RGB")
            picture.thumbnail((_SIZE, _SIZE))
            out = BytesIO()
            picture.save(out, "JPEG", quality=82, optimize=True)
            return out.getvalue()
    except Exception:  # noqa: BLE001 - a picture is never worth losing the offer over
        _LOGGER.debug("Could not cut a picture out of a brochure page", exc_info=True)
        return None


def file_name(offer_id: str) -> str:
    return offer_id.replace(":", "_").replace("/", "_") + ".jpg"
