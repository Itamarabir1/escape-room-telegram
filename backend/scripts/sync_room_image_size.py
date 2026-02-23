#!/usr/bin/env python3
"""
Reads the room image size (images/escape_room.png or latest escape_room_*.png)
and updates backend/data/demo_room.py: DEMO_ROOM_WIDTH, DEMO_ROOM_HEIGHT,
and converts each item's x,y from the previous canvas size to the new one.
Run from repo root: python backend/scripts/sync_room_image_size.py
"""
from __future__ import annotations

import re
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def find_room_image(root: Path) -> Path | None:
    images_dir = root / "images"
    if not images_dir.is_dir():
        return None
    primary = images_dir / "escape_room.png"
    if primary.is_file():
        return primary
    candidates = sorted(images_dir.glob("escape_room_*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def get_image_size(path: Path) -> tuple[int, int]:
    try:
        from PIL import Image
    except ImportError:
        raise SystemExit("Install Pillow: pip install Pillow")
    with Image.open(path) as im:
        return (im.width, im.height)


def read_current_demo_constants(demo_path: Path) -> tuple[int, int]:
    text = demo_path.read_text(encoding="utf-8")
    w = re.search(r"DEMO_ROOM_WIDTH\s*=\s*(\d+)", text)
    h = re.search(r"DEMO_ROOM_HEIGHT\s*=\s*(\d+)", text)
    if not w or not h:
        return (1600, 1200)
    return (int(w.group(1)), int(h.group(1)))


def update_demo_room(demo_path: Path, new_w: int, new_h: int, old_w: int, old_h: int) -> None:
    text = demo_path.read_text(encoding="utf-8")

    text = re.sub(r"(DEMO_ROOM_WIDTH\s*=\s*)\d+", rf"\g<1>{new_w}", text, count=1)
    text = re.sub(r"(DEMO_ROOM_HEIGHT\s*=\s*)\d+", rf"\g<1>{new_h}", text, count=1)

    def convert_coords(m: re.Match) -> str:
        x = int(m.group(1))
        y = int(m.group(2))
        nx = round(x * new_w / old_w)
        ny = round(y * new_h / old_h)
        return f'"x": {nx}, "y": {ny}'

    text = re.sub(r'"x":\s*(\d+),\s*"y":\s*(\d+)', convert_coords, text)
    demo_path.write_text(text, encoding="utf-8")


def main() -> None:
    root = repo_root()
    img_path = find_room_image(root)
    if not img_path:
        raise SystemExit("No room image found under images/ (escape_room.png or escape_room_*.png)")

    width, height = get_image_size(img_path)
    print(f"Image: {img_path.relative_to(root)} -> {width} x {height}")

    demo_path = root / "backend" / "data" / "demo_room.py"
    if not demo_path.is_file():
        raise SystemExit(f"Not found: {demo_path}")

    old_w, old_h = read_current_demo_constants(demo_path)
    if (old_w, old_h) == (width, height):
        print("demo_room.py already has this size, nothing to do.")
        return

    update_demo_room(demo_path, width, height, old_w, old_h)
    print(f"Updated {demo_path.relative_to(root)}: size {old_w}x{old_h} -> {width}x{height}, item coords converted.")


if __name__ == "__main__":
    main()
