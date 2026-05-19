"""Split a transparent sprite sheet into individual PNGs by alpha-channel connected components.

Usage:
    python scripts/split_sheet.py assets/aeyong/sheet.png assets/aeyong
"""

from __future__ import annotations

import sys
from collections import deque
from pathlib import Path

from PIL import Image


ALPHA_THRESHOLD = 16
MIN_AREA = 2000


def find_components(alpha_bytes: bytes, width: int, height: int) -> list[tuple[int, int, int, int]]:
    visited = bytearray(width * height)
    boxes: list[tuple[int, int, int, int]] = []

    for start_y in range(height):
        row_offset = start_y * width
        for start_x in range(width):
            index = row_offset + start_x
            if visited[index]:
                continue
            if alpha_bytes[index] <= ALPHA_THRESHOLD:
                visited[index] = 1
                continue

            min_x, min_y, max_x, max_y = start_x, start_y, start_x, start_y
            area = 0
            stack: deque[tuple[int, int]] = deque()
            stack.append((start_x, start_y))
            visited[index] = 1

            while stack:
                x, y = stack.pop()
                area += 1
                if x < min_x:
                    min_x = x
                if x > max_x:
                    max_x = x
                if y < min_y:
                    min_y = y
                if y > max_y:
                    max_y = y

                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)):
                    nx, ny = x + dx, y + dy
                    if not (0 <= nx < width and 0 <= ny < height):
                        continue
                    nindex = ny * width + nx
                    if visited[nindex]:
                        continue
                    if alpha_bytes[nindex] <= ALPHA_THRESHOLD:
                        visited[nindex] = 1
                        continue
                    visited[nindex] = 1
                    stack.append((nx, ny))

            if area >= MIN_AREA:
                boxes.append((min_x, min_y, max_x + 1, max_y + 1))

    return boxes


def merge_overlapping(boxes: list[tuple[int, int, int, int]], gap: int = 10) -> list[tuple[int, int, int, int]]:
    merged: list[tuple[int, int, int, int]] = []
    for box in boxes:
        x1, y1, x2, y2 = box
        absorbed = False
        for i, (mx1, my1, mx2, my2) in enumerate(merged):
            if x1 < mx2 + gap and x2 > mx1 - gap and y1 < my2 + gap and y2 > my1 - gap:
                merged[i] = (min(x1, mx1), min(y1, my1), max(x2, mx2), max(y2, my2))
                absorbed = True
                break
        if not absorbed:
            merged.append(box)

    changed = True
    while changed:
        changed = False
        out: list[tuple[int, int, int, int]] = []
        for box in merged:
            x1, y1, x2, y2 = box
            placed = False
            for i, (mx1, my1, mx2, my2) in enumerate(out):
                if x1 < mx2 + gap and x2 > mx1 - gap and y1 < my2 + gap and y2 > my1 - gap:
                    out[i] = (min(x1, mx1), min(y1, my1), max(x2, mx2), max(y2, my2))
                    placed = True
                    changed = True
                    break
            if not placed:
                out.append(box)
        merged = out
    return merged


def sort_grid(boxes: list[tuple[int, int, int, int]]) -> list[tuple[int, int, int, int]]:
    if not boxes:
        return boxes
    heights = [(y2 - y1) for _, y1, _, y2 in boxes]
    row_gap = max(heights) * 0.5
    rows: list[list[tuple[int, int, int, int]]] = []
    for box in sorted(boxes, key=lambda b: b[1]):
        if rows and box[1] - rows[-1][-1][1] < row_gap:
            rows[-1].append(box)
        else:
            rows.append([box])
    ordered: list[tuple[int, int, int, int]] = []
    for row in rows:
        row.sort(key=lambda b: b[0])
        ordered.extend(row)
    return ordered


def main() -> None:
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    sheet_path = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)

    image = Image.open(sheet_path).convert("RGBA")
    width, height = image.size
    alpha = image.split()[3].tobytes()

    raw_boxes = find_components(alpha, width, height)
    print(f"raw components (>= {MIN_AREA}px): {len(raw_boxes)}")

    ordered = sort_grid(raw_boxes)

    for index, (x1, y1, x2, y2) in enumerate(ordered, start=1):
        crop = image.crop((x1, y1, x2, y2))
        out_path = out_dir / f"pose_{index}.png"
        crop.save(out_path)
        print(f"pose_{index}.png  bbox=({x1},{y1},{x2},{y2})  size=({x2 - x1}x{y2 - y1})")


if __name__ == "__main__":
    main()
