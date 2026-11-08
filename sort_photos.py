#!/usr/bin/env python3
"""Index a folder of photos by label ID and link them into one folder per part.

Originals are only read. The output holds index.csv and symbolic links, so deleting it never
touches a photo. Photos already in the index are skipped unless --rescan is given.
"""
import argparse
import csv
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from PIL import Image, ImageOps

from read_photo import load_known, read_image

EXTENSIONS = {".heic", ".heif", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}
FIELDS = ["photo", "id", "method", "px_per_module", "known"]


def scan_photo(path: Path) -> tuple[Path, dict | None, str | None]:
    """Return the IDs found in one photo, or an error text if it cannot be read."""
    try:
        image = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
        return path, read_image(image), None
    except Exception as exc:  # A broken file must not stop a long batch.
        return path, None, f"{type(exc).__name__}: {exc}"


def load_index(index_path: Path) -> list[dict]:
    if not index_path.exists():
        return []
    with index_path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_index(index_path: Path, rows: list[dict]) -> None:
    temp_path = index_path.with_suffix(".tmp")
    with temp_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda row: (row["photo"], row["id"])))
    temp_path.replace(index_path)


def rebuild_links(output: Path, rows: list[dict]) -> None:
    """Recreate parts/ and unmatched/, removing only symbolic links and empty folders."""
    for folder_name in ("parts", "unmatched"):
        folder = output / folder_name
        if not folder.exists():
            continue
        for root, dirs, files in os.walk(folder, topdown=False):
            for name in files + dirs:
                entry = Path(root) / name
                if entry.is_symlink():
                    entry.unlink()
                elif entry.is_dir():
                    entry.rmdir()
    for row in rows:
        target = output / "parts" / row["id"] if row["id"] else output / "unmatched"
        target.mkdir(parents=True, exist_ok=True)
        photo = Path(row["photo"])
        (target / photo.name).symlink_to(photo)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("photos", type=Path, help="folder with photos, not searched recursively")
    parser.add_argument("--out", type=Path, help="output folder, default <photos>-sorted next to the photo folder")
    parser.add_argument("--rescan", action="store_true", help="scan photos again that are already in the index")
    parser.add_argument("--jobs", type=int, default=min(4, os.cpu_count() or 1), help="photos scanned in parallel")
    args = parser.parse_args()

    photo_dir = args.photos.expanduser().resolve()
    if not photo_dir.is_dir():
        raise SystemExit(f"{photo_dir} is not a folder")
    output = (args.out.expanduser().resolve() if args.out else photo_dir.with_name(f"{photo_dir.name}-sorted"))
    output.mkdir(parents=True, exist_ok=True)
    index_path = output / "index.csv"

    photos = sorted(p for p in photo_dir.iterdir() if p.is_file() and p.suffix.lower() in EXTENSIONS)
    existing = {str(p) for p in photos}
    # Rows of removed photos are dropped, so no dead links remain.
    rows = [row for row in load_index(index_path) if row["photo"] in existing]
    if args.rescan:
        rows = []
    done = {row["photo"] for row in rows}
    todo = [p for p in photos if str(p) not in done]
    print(f"{len(photos)} photos, {len(todo)} to scan")

    known = load_known()
    failed = 0
    with ProcessPoolExecutor(max_workers=max(args.jobs, 1)) as pool:
        futures = [pool.submit(scan_photo, path) for path in todo]
        for number, future in enumerate(as_completed(futures), 1):
            path, found, error = future.result()
            if error:
                # Not added to the index, so the next run tries this photo again.
                failed += 1
                print(f"[{number}/{len(todo)}] {path.name}: FAILED {error}")
                continue
            for value, (how, px) in sorted(found.items()):
                rows.append(
                    {
                        "photo": str(path),
                        "id": value,
                        "method": how,
                        "px_per_module": f"{px:.1f}" if px else "",
                        "known": "yes" if value in known else "no",
                    }
                )
            if not found:
                rows.append({"photo": str(path), "id": "", "method": "", "px_per_module": "", "known": ""})
            print(f"[{number}/{len(todo)}] {path.name}: {len(found)} IDs")
            # Saved after each photo, so an interrupted batch keeps its progress.
            write_index(index_path, rows)

    write_index(index_path, rows)
    rebuild_links(output, rows)
    parts = {row["id"] for row in rows if row["id"]}
    unmatched = sum(1 for row in rows if not row["id"])
    unknown = {row["id"] for row in rows if row["known"] == "no"}
    print(f"{len(parts)} parts, {unmatched} photos without ID, {failed} failed, {len(unknown)} IDs not in the print log")
    print(f"output: {output}")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
