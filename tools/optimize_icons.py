"""Losslessly recompress icons and cap oversized source art for the web UI.

Run from the project root after adding or replacing icons:
    python tools/optimize_icons.py

Pillow is only needed for this maintenance command, not by the application.
"""
from pathlib import Path

from PIL import Image


ICON_ROOT = Path(__file__).resolve().parent.parent / "frontend" / "icons"
MAX_PIXEL_SIZE = 128  # Largest UI icon is 54 px; this remains retina-sharp.


def optimize_icon(path: Path) -> tuple[int, int, bool]:
    original_bytes = path.stat().st_size
    temporary = path.with_name(f"{path.stem}.optimized{path.suffix}")

    with Image.open(path) as source:
        source.load()
        image = source.copy()
    resized = max(image.size) > MAX_PIXEL_SIZE
    if resized:
        image.thumbnail(
            (MAX_PIXEL_SIZE, MAX_PIXEL_SIZE),
            Image.Resampling.LANCZOS,
        )
    image.save(temporary, format="PNG", optimize=True, compress_level=9)

    optimized_bytes = temporary.stat().st_size
    if resized or optimized_bytes < original_bytes:
        temporary.replace(path)
        return original_bytes, optimized_bytes, True
    temporary.unlink()
    return original_bytes, original_bytes, False


def main() -> None:
    before = after = changed = 0
    for path in sorted(ICON_ROOT.rglob("*.png")):
        old_size, new_size, was_changed = optimize_icon(path)
        before += old_size
        after += new_size
        changed += int(was_changed)
    saved = before - after
    print(
        f"Optimized {changed} icons: "
        f"{before / 1024:.1f} KiB -> {after / 1024:.1f} KiB "
        f"({saved / 1024:.1f} KiB saved)"
    )


if __name__ == "__main__":
    main()
