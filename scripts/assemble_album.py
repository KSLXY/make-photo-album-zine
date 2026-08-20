#!/usr/bin/env python3
"""Assemble validated 3:5 album page images into one ordered PDF."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any


def _pillow() -> Any:
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("assemble_album.py requires Pillow.") from exc
    return Image


def assemble(plan: dict[str, Any], output: Path, quality: int = 95) -> dict[str, Any]:
    Image = _pillow()
    pages = plan.get("pages")
    if not isinstance(pages, list) or not pages:
        raise ValueError("Plan contains no pages.")
    ordered = sorted(pages, key=lambda item: item.get("page", 0))
    numbers = [item.get("page") for item in ordered]
    if numbers != list(range(1, len(ordered) + 1)):
        raise ValueError("Page numbers must be sequential starting at 1.")
    if not 80 <= quality <= 100:
        raise ValueError("quality must be between 80 and 100.")

    images = []
    sources = []
    try:
        for page in ordered:
            rendered = page.get("rendered_path")
            if not isinstance(rendered, str) or not rendered.strip():
                raise ValueError(f"Page {page.get('page')} has no rendered_path.")
            path = Path(rendered)
            if not path.is_file():
                raise FileNotFoundError(path)
            with Image.open(path) as source:
                source.load()
                width, height = source.size
                if width <= 0 or height <= 0:
                    raise ValueError(f"Invalid image dimensions: {path}")
                ratio = width / height
                if abs(ratio - 0.6) > 0.002:
                    raise ValueError(f"Page is not 3:5 portrait: {path} ({width}x{height})")
                images.append(source.convert("RGB"))
                sources.append(str(path))

        output.parent.mkdir(parents=True, exist_ok=True)
        temp_output = output.with_name(f".{output.stem}.tmp.pdf")
        try:
            images[0].save(
                temp_output,
                format="PDF",
                save_all=True,
                append_images=images[1:],
                resolution=300.0,
                quality=quality,
                subsampling=0,
                title=str(plan.get("album_title") or "Photo Album"),
                author="make-photo-album-zine",
            )
            if not temp_output.is_file() or temp_output.stat().st_size < 1000:
                raise RuntimeError("PDF creation produced an empty or invalid file.")
            verified_count = None
            try:
                from pypdf import PdfReader

                verified_count = len(PdfReader(str(temp_output)).pages)
                if verified_count != len(ordered):
                    raise RuntimeError(
                        f"PDF page count mismatch: expected {len(ordered)}, got {verified_count}."
                    )
            except ImportError:
                verified_count = None
            temp_output.replace(output)
        finally:
            temp_output.unlink(missing_ok=True)
    finally:
        for image in images:
            image.close()

    return {
        "ok": True,
        "output": str(output),
        "page_count": len(ordered),
        "verified_page_count": verified_count,
        "sources": sources,
    }


def run_self_test() -> None:
    Image = _pillow()
    with tempfile.TemporaryDirectory(prefix="album-assemble-") as temp_dir:
        root = Path(temp_dir)
        pages = []
        for index, color in enumerate(((215, 150, 105), (95, 125, 135), (165, 175, 150)), start=1):
            path = root / f"page-{index:03d}.png"
            Image.new("RGB", (600, 1000), color).save(path)
            pages.append({"page": index, "rendered_path": str(path)})
        output = root / "album.pdf"
        result = assemble({"album_title": "Self Test", "pages": pages}, output)
        assert result["page_count"] == 3
        assert output.stat().st_size > 1000
        print(json.dumps({"ok": True, "tests": 3}, ensure_ascii=False))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", help="Path to rendered album plan")
    parser.add_argument("--output", help="Output PDF path")
    parser.add_argument("--quality", type=int, default=95)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        run_self_test()
        return 0
    if not args.plan or not args.output:
        parser.error("--plan and --output are required unless --self-test is used")
    try:
        plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
        result = assemble(plan, Path(args.output), quality=args.quality)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
