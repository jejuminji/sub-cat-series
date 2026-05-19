"""PNG sprite loading and caching for cat styles backed by image assets."""

from __future__ import annotations

from pathlib import Path

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


POSE_FILES = {
    "idle": "pose_1.png",
    "walk_away": "pose_2.png",
    "nap": "pose_3.png",
    "alert": "pose_4.png",
    "walk": "pose_5.png",
    "idle_small": "pose_6.png",
    "talk": "pose_7.png",
    "play": "pose_8.png",
}


def _harden_edges(image, matte_color: tuple[int, int, int], alpha_cutoff: int = 40):
    """Composite semi-transparent pixels onto a matte color and threshold alpha to 0/255.

    Avoids the color-key fringe that appears when tkinter alpha-blends sprite edges with
    the canvas background and Windows `-transparentcolor` then fails to strip the blended
    pixels.
    """
    if image.mode != "RGBA":
        return image
    matte = Image.new("RGBA", image.size, matte_color + (255,))
    composited = Image.alpha_composite(matte, image)
    r, g, b, _ = composited.split()
    new_alpha = image.split()[3].point(lambda px: 255 if px > alpha_cutoff else 0)
    return Image.merge("RGBA", (r, g, b, new_alpha))


class SpriteSet:
    """Cache scaled, optionally flipped PhotoImage objects for one cat style."""

    def __init__(
        self,
        folder: Path,
        max_height: int = 128,
        matte_color: tuple[int, int, int] = (245, 240, 230),
        alpha_cutoff: int = 40,
    ) -> None:
        self.folder = Path(folder)
        self.max_height = max_height
        self._raw: dict[str, object] = {}
        self._photos: dict[tuple[str, int], object] = {}
        self.available = False
        if not PIL_AVAILABLE:
            return
        for pose, filename in POSE_FILES.items():
            path = self.folder / filename
            if not path.exists():
                continue
            try:
                image = Image.open(path).convert("RGBA")
            except (OSError, ValueError):
                continue
            w, h = image.size
            if h > max_height:
                ratio = max_height / h
                image = image.resize((max(1, int(w * ratio)), max_height), Image.LANCZOS)
            image = _harden_edges(image, matte_color, alpha_cutoff)
            self._raw[pose] = image
        self.available = bool(self._raw)

    def photo(self, pose: str, facing: int):
        if not self.available:
            return None
        image = self._raw.get(pose) or self._raw.get("idle")
        if image is None:
            return None
        key = (pose, 1 if facing >= 0 else -1)
        cached = self._photos.get(key)
        if cached is not None:
            return cached
        rendered = image if facing >= 0 else image.transpose(Image.FLIP_LEFT_RIGHT)
        photo = ImageTk.PhotoImage(rendered)
        self._photos[key] = photo
        return photo

    def size(self, pose: str) -> tuple[int, int]:
        image = self._raw.get(pose)
        if image is None:
            return (0, 0)
        return image.size
