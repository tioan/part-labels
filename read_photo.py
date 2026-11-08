#!/usr/bin/env python3
"""Find label IDs in photos: a direct zxing-cpp pass, then tiled and preprocessed passes."""
import json
import re
import sys
from pathlib import Path

import zxingcpp
from PIL import Image, ImageFilter, ImageOps

STRIPS = Path(__file__).parent / "strips"
ID_PATTERN = re.compile(r"^[0-9A-HJKMNP-TV-Z]{10}$")
MODULES = {"QRCode": 21, "DataMatrix": 14}

# Different variants recover different codes, so all of them run.
VARIANTS = {
    "plain": lambda tile: tile,
    "contrast": lambda tile: ImageOps.autocontrast(tile, cutoff=1),
    "denoise": lambda tile: ImageOps.autocontrast(tile.filter(ImageFilter.MedianFilter(3)), cutoff=1),
    "blur": lambda tile: ImageOps.autocontrast(tile.filter(ImageFilter.GaussianBlur(1.2)), cutoff=1),
}


def load_known() -> dict:
    known = {}
    manifest = STRIPS / "manifest.json"
    if manifest.exists():
        known.update({e["id"]: e for e in json.loads(manifest.read_text())})
    issued = STRIPS / "issued.jsonl"
    if issued.exists():
        for line in issued.read_text().splitlines():
            entry = json.loads(line)
            known[entry["id"]] = entry
    return known


def px_per_module(result) -> float | None:
    modules = MODULES.get(result.format.name)
    if modules is None:
        return None
    pos = result.position
    side = ((pos.top_left.x - pos.top_right.x) ** 2 + (pos.top_left.y - pos.top_right.y) ** 2) ** 0.5
    return side / modules


def read_image(image: Image.Image) -> dict:
    """Return id -> (how it was found, px per module if measured in the original scale)."""
    found = {}

    def add(results, how, scale):
        for result in results:
            if ID_PATTERN.match(result.text) and result.text not in found:
                px = px_per_module(result)
                found[result.text] = (how, px / scale if px else None)

    add(zxingcpp.read_barcodes(image), "direct", 1)
    gray = image.convert("L")
    # Tiles scale with the image, so chat-sized and original photos get a similar coverage.
    size = max(gray.size) // 4
    step = size // 2
    for factor in (1, 2):
        for name, process in VARIANTS.items():
            for top in range(0, max(gray.height - step, 1), step):
                for left in range(0, max(gray.width - step, 1), step):
                    tile = gray.crop((left, top, left + size, top + size))
                    if factor > 1:
                        tile = tile.resize((tile.width * factor, tile.height * factor), Image.LANCZOS)
                    add(zxingcpp.read_barcodes(process(tile)), f"tile x{factor} {name}", factor)
    return found


def main() -> None:
    known = load_known()
    for name in sys.argv[1:]:
        image = ImageOps.exif_transpose(Image.open(name)).convert("RGB")
        found = read_image(image)
        direct = sum(1 for how, _ in found.values() if how == "direct")
        print(f"{Path(name).name}: {image.width}x{image.height}, {len(found)} IDs, {direct} direct")
        for value, (how, px) in sorted(found.items()):
            entry = known.get(value)
            if entry:
                label = f"{entry['kind']} {entry['dots_per_module']} dots on {entry['tape_mm']} mm"
            else:
                label = "unknown ID"
            size = f"{px:.1f} px/module" if px else "size unknown"
            print(f"  {value}  {label}  {how}  {size}")


if __name__ == "__main__":
    main()
