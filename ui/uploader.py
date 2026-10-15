"""Pure-Python logic behind the multi-image portrait uploader.

Nothing here imports Gradio, so it is easy to unit-test. The state is just
``images`` (a list of file paths, max ``MAX_IMAGES``) and ``active`` (index of the
photo currently shown on the stage).
"""
from __future__ import annotations

import base64
import io
import os
from typing import Iterable, List, Optional, Sequence, Tuple

from PIL import Image, ImageEnhance, ImageDraw, ImageOps, UnidentifiedImageError

MAX_IMAGES = 5
MAX_FILE_BYTES = 20 * 1024 * 1024          # reject anything larger than 20 MB
PORTRAIT_RATIO = (3, 4)                    # width : height of the stage + thumbnails
STAGE_SIZE = (600, 800)
THUMB_SIZE = (150, 200)
MODEL_MAX_SIDE = 1568                      # longest side sent to the vision model
ACCENT = (255, 122, 26)


# --------------------------------------------------------------------------- #
# Input normalisation / validation
# --------------------------------------------------------------------------- #
def to_paths(files) -> List[str]:
    """Accept whatever Gradio hands us (None, str, list, file objects) -> list of paths."""
    if files is None:
        return []
    if not isinstance(files, (list, tuple)):
        files = [files]
    paths = []
    for f in files:
        if f is None:
            continue
        if isinstance(f, str):
            paths.append(f)
        elif isinstance(f, dict) and f.get("path"):
            paths.append(f["path"])
        elif hasattr(f, "name"):
            paths.append(f.name)
    return paths


def is_valid_image(path: str) -> bool:
    try:
        if os.path.getsize(path) > MAX_FILE_BYTES:
            return False
        with Image.open(path) as im:
            im.verify()
        return True
    except (OSError, UnidentifiedImageError, ValueError):
        return False


def _split_valid(paths: Iterable[str]) -> Tuple[List[str], int]:
    """Return (valid paths, number skipped)."""
    paths = list(paths)
    good = [p for p in paths if is_valid_image(p)]
    return good, len(paths) - len(good)


# --------------------------------------------------------------------------- #
# State transitions  (each returns new_images, new_active, notices)
# --------------------------------------------------------------------------- #
def add_images(new_paths: Sequence[str], images: Sequence[str], active: int):
    """Append photos, enforcing the MAX_IMAGES limit. New photo becomes active."""
    images = list(images)
    notices: List[str] = []
    good, skipped = _split_valid(new_paths)
    if skipped:
        notices.append(f"Skipped {skipped} file{'s' if skipped != 1 else ''} that "
                       f"{'are' if skipped != 1 else 'is'} not a supported image (or over 20 MB).")
    room = MAX_IMAGES - len(images)
    if len(good) > room:
        notices.append(f"You can add up to {MAX_IMAGES} photos - "
                       f"{len(good) - room} extra {'were' if len(good) - room != 1 else 'was'} ignored.")
        good = good[:max(room, 0)]
    if good:
        images.extend(good)
        active = len(images) - len(good)       # jump to the first newly added photo
    return images, _clamp(active, images), notices


def replace_image(new_path: Optional[str], images: Sequence[str], active: int):
    """Swap the active photo for a new one."""
    images = list(images)
    notices: List[str] = []
    if not images or not new_path:
        return images, _clamp(active, images), notices
    if not is_valid_image(new_path):
        notices.append("That file is not a supported image (or is over 20 MB).")
        return images, _clamp(active, images), notices
    active = _clamp(active, images)
    images[active] = new_path
    return images, active, notices


def delete_image(images: Sequence[str], active: int):
    """Remove the active photo; keep the selection on a neighbouring photo."""
    images = list(images)
    if images:
        active = _clamp(active, images)
        images.pop(active)
    return images, _clamp(active, images), []


def select_image(index: Optional[int], images: Sequence[str]):
    return list(images), _clamp(index or 0, images), []


def _clamp(index: int, images: Sequence[str]) -> int:
    if not images:
        return 0
    return max(0, min(int(index), len(images) - 1))


# --------------------------------------------------------------------------- #
# Rendering helpers (fixed portrait aspect ratio via centre-cover crop)
# --------------------------------------------------------------------------- #
def _open_oriented(path: str) -> Image.Image:
    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im)
        return im.convert("RGB")


def cover_crop(path: str, size: Tuple[int, int]) -> Image.Image:
    """Fill ``size`` completely, cropping the overflow (CSS ``object-fit: cover``)."""
    return ImageOps.fit(_open_oriented(path), size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))


def stage_data_uri(path: str, size: Tuple[int, int] = STAGE_SIZE) -> str:
    """JPEG data-URI of the portrait-cropped stage image (embedded in the stage HTML)."""
    buf = io.BytesIO()
    cover_crop(path, size).save(buf, format="JPEG", quality=84, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def thumbnails(images: Sequence[str], active: int) -> List[Image.Image]:
    """Portrait thumbnails; the active one gets a baked-in orange frame, others are dimmed."""
    out = []
    for i, path in enumerate(images):
        thumb = cover_crop(path, THUMB_SIZE)
        if i == active:
            draw = ImageDraw.Draw(thumb)
            w, h = thumb.size
            for k in range(5):
                draw.rectangle([k, k, w - 1 - k, h - 1 - k], outline=ACCENT)
        else:
            thumb = ImageEnhance.Brightness(thumb).enhance(0.55)
        out.append(thumb)
    return out


def prepare_for_model(paths: Sequence[str], out_dir: str) -> List[str]:
    """Normalise photos for the vision model: apply EXIF rotation, convert to RGB JPEG,
    cap the longest side. Originals are never modified."""
    prepared = []
    for i, p in enumerate(paths, 1):
        im = _open_oriented(p)
        im.thumbnail((MODEL_MAX_SIDE, MODEL_MAX_SIDE), Image.Resampling.LANCZOS)
        dest = os.path.join(out_dir, f"photo-{i}.jpg")
        im.save(dest, format="JPEG", quality=88)
        prepared.append(dest)
    return prepared
