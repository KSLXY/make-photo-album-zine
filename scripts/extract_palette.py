#!/usr/bin/env python3
"""Extract source-faithful album palette candidates from local photographs."""

from __future__ import annotations

import argparse
import colorsys
import json
import math
import sys
import tempfile
from pathlib import Path
from typing import Any


def _pillow() -> tuple[Any, Any]:
    try:
        from PIL import Image, ImageOps
    except ImportError as exc:
        raise RuntimeError("extract_palette.py requires Pillow.") from exc
    return Image, ImageOps


def _hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def _luminance(rgb: tuple[int, int, int]) -> float:
    channels = []
    for value in rgb:
        channel = value / 255.0
        channels.append(channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def _saturation(rgb: tuple[int, int, int]) -> float:
    return colorsys.rgb_to_hsv(*(value / 255.0 for value in rgb))[1]


def _distance(first: tuple[int, int, int], second: tuple[int, int, int]) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(first, second)))


def _blend(
    source: tuple[int, int, int],
    target: tuple[int, int, int],
    target_weight: float,
) -> tuple[int, int, int]:
    return tuple(
        round(source[index] * (1.0 - target_weight) + target[index] * target_weight)
        for index in range(3)
    )


def _quantized_colors(path: Path, color_count: int = 12) -> list[dict[str, Any]]:
    Image, ImageOps = _pillow()
    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
        image.thumbnail((256, 256), Image.Resampling.LANCZOS)
        quantized = image.quantize(colors=color_count, method=Image.Quantize.MEDIANCUT)
        palette = quantized.getpalette()
        counts = quantized.getcolors(maxcolors=color_count) or []

    total = sum(count for count, _ in counts) or 1
    colors: list[dict[str, Any]] = []
    for count, palette_index in sorted(counts, reverse=True):
        offset = palette_index * 3
        rgb = tuple(palette[offset : offset + 3])
        if len(rgb) != 3:
            continue
        typed_rgb = (int(rgb[0]), int(rgb[1]), int(rgb[2]))
        colors.append(
            {
                "rgb": typed_rgb,
                "hex": _hex(typed_rgb),
                "share": round(count / total, 4),
                "luminance": round(_luminance(typed_rgb), 4),
                "saturation": round(_saturation(typed_rgb), 4),
            }
        )
    if not colors:
        raise ValueError(f"No colors could be extracted from {path}")
    return colors


def extract_palette(path: Path) -> dict[str, Any]:
    colors = _quantized_colors(path)
    useful = [item for item in colors if 0.035 <= item["luminance"] <= 0.94]
    if not useful:
        useful = colors

    dominant = max(useful, key=lambda item: item["share"])
    dominant_rgb = dominant["rgb"]

    support_candidates = [
        item for item in useful if _distance(item["rgb"], dominant_rgb) >= 34
    ]
    support = max(support_candidates or useful, key=lambda item: item["share"])

    dark_candidates = [item for item in colors if item["luminance"] <= 0.42]
    if dark_candidates:
        dark_rgb = min(dark_candidates, key=lambda item: item["luminance"])["rgb"]
    else:
        dark_rgb = _blend(dominant_rgb, (28, 30, 30), 0.62)

    accent_candidates = [
        item for item in useful if 0.06 <= item["luminance"] <= 0.86
    ]
    accent = max(
        accent_candidates or useful,
        key=lambda item: item["saturation"] * math.sqrt(item["share"] + 0.002),
    )
    if accent["saturation"] < 0.16:
        accent = support

    paper_rgb = _blend(dominant_rgb, (245, 241, 233), 0.86)
    warm_score = dominant_rgb[0] - dominant_rgb[2]
    temperature = "warm" if warm_score > 18 else "cool" if warm_score < -18 else "neutral"

    return {
        "paper": _hex(paper_rgb),
        "dominant": dominant["hex"],
        "support": support["hex"],
        "accent": accent["hex"],
        "dark": _hex(dark_rgb),
        "temperature": temperature,
        "candidates": [
            {"hex": item["hex"], "share": item["share"]} for item in colors[:8]
        ],
    }


def run_self_test() -> None:
    Image, _ = _pillow()
    with tempfile.TemporaryDirectory(prefix="album-palette-") as temp_dir:
        path = Path(temp_dir) / "fixture.png"
        image = Image.new("RGB", (300, 200), (76, 112, 132))
        for x in range(190, 300):
            for y in range(200):
                image.putpixel((x, y), (202, 132, 70))
        for x in range(40):
            for y in range(200):
                image.putpixel((x, y), (28, 38, 41))
        image.save(path)
        result = extract_palette(path)
        for key in ("paper", "dominant", "support", "accent", "dark"):
            value = result[key]
            assert isinstance(value, str) and len(value) == 7 and value.startswith("#")
        assert result["temperature"] in {"warm", "cool", "neutral"}
        print(json.dumps({"ok": True, "tests": 6, "palette": result}, ensure_ascii=False))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("photos", nargs="*", help="Local photo paths in stable order")
    parser.add_argument("--output", help="Output JSON path")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        run_self_test()
        return 0
    if not args.photos or not args.output:
        parser.error("photos and --output are required unless --self-test is used")

    results = []
    try:
        for index, raw_path in enumerate(args.photos, start=1):
            path = Path(raw_path).resolve()
            if not path.is_file():
                raise FileNotFoundError(path)
            results.append(
                {
                    "id": f"p{index:03d}",
                    "path": str(path),
                    "palette": extract_palette(path),
                }
            )
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps({"photos": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1

    print(json.dumps({"ok": True, "output": str(output), "photo_count": len(results)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
