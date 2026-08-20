#!/usr/bin/env python3
"""Composite unchanged photos, source-colored backgrounds, and edge stickers."""

from __future__ import annotations

import argparse
import copy
import json
import math
import sys
import tempfile
from pathlib import Path
from typing import Any


PAGE_W = 1800
PAGE_H = 3000
MAT_PADDING = 18


def _pillow() -> tuple[Any, Any, Any, Any]:
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageOps
    except ImportError as exc:
        raise RuntimeError("compose_album_pages.py requires Pillow.") from exc
    return Image, ImageDraw, ImageFont, ImageOps


def _rgb(hex_color: str) -> tuple[int, int, int]:
    value = hex_color.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def _rgba(hex_color: str, alpha: int) -> tuple[int, int, int, int]:
    return (*_rgb(hex_color), alpha)


def _load_rgb(path: Path) -> Any:
    Image, _, _, ImageOps = _pillow()
    with Image.open(path) as source:
        return ImageOps.exif_transpose(source).convert("RGB")


def _atomic_save_png(image: Any, path: Path) -> None:
    Image, _, _, _ = _pillow()
    temp_path = path.with_name(f".{path.stem}.tmp.png")
    try:
        image.save(temp_path, format="PNG", compress_level=6)
        with Image.open(temp_path) as check:
            check.load()
            if check.size != image.size:
                raise ValueError(f"PNG verification failed: {path}")
        temp_path.replace(path)
    finally:
        temp_path.unlink(missing_ok=True)
    with Image.open(path) as check:
        check.load()


def _placement_center(name: str) -> tuple[int, int]:
    return {
        "upper-left": (360, 500),
        "upper-right": (1440, 500),
        "center-left": (350, 1500),
        "center-right": (1450, 1500),
        "lower-left": (360, 2500),
        "lower-right": (1440, 2500),
    }[name]


def _draw_element(overlay: Any, element: dict[str, Any], palette: dict[str, str]) -> None:
    _, ImageDraw, _, _ = _pillow()
    draw = ImageDraw.Draw(overlay, "RGBA")
    center_x, center_y = _placement_center(element["placement"])
    alpha = round(255 * element["opacity"] / 100)
    color = _rgba(palette[element["color_role"]], alpha)
    kind = element["kind"]

    if kind == "wash":
        draw.ellipse((center_x - 520, center_y - 360, center_x + 520, center_y + 360), fill=color)
    elif kind == "arch":
        for offset in range(0, 90, 22):
            draw.arc(
                (center_x - 300 - offset, center_y - 250 - offset, center_x + 300 + offset, center_y + 360 + offset),
                190,
                350,
                fill=color,
                width=8,
            )
    elif kind == "wave":
        for row in range(4):
            points = []
            for step in range(121):
                x = center_x - 420 + step * 7
                y = center_y + row * 44 + math.sin(step / 9.0) * 28
                points.append((x, y))
            draw.line(points, fill=color, width=7)
    elif kind == "disc":
        draw.ellipse((center_x - 260, center_y - 260, center_x + 260, center_y + 260), outline=color, width=18)
        draw.ellipse((center_x - 150, center_y - 150, center_x + 150, center_y + 150), outline=color, width=8)
    elif kind == "grid":
        for offset in range(-300, 301, 100):
            draw.line((center_x + offset, center_y - 340, center_x + offset, center_y + 340), fill=color, width=5)
        for offset in range(-300, 301, 100):
            draw.line((center_x - 340, center_y + offset, center_x + 340, center_y + offset), fill=color, width=5)
    elif kind == "leaf":
        for angle, distance in ((-40, 0), (-10, 110), (25, 210)):
            leaf_x = center_x + round(math.cos(math.radians(angle)) * distance)
            leaf_y = center_y + round(math.sin(math.radians(angle)) * distance)
            draw.ellipse((leaf_x - 90, leaf_y - 38, leaf_x + 90, leaf_y + 38), fill=color)
        draw.line((center_x - 130, center_y + 160, center_x + 280, center_y - 140), fill=color, width=7)
    elif kind == "tape":
        draw.rounded_rectangle((center_x - 300, center_y - 70, center_x + 300, center_y + 70), radius=18, fill=color)
    elif kind == "frame":
        draw.rounded_rectangle((center_x - 360, center_y - 430, center_x + 360, center_y + 430), radius=28, outline=color, width=10)


def _background(page_spec: dict[str, Any]) -> Any:
    Image, _, _, ImageOps = _pillow()
    palette = page_spec["palette"]
    background = page_spec["background"]
    if background["mode"] == "asset":
        path = Path(background["rendered_path"])
        with Image.open(path) as source:
            return ImageOps.fit(source.convert("RGB"), (PAGE_W, PAGE_H), method=Image.Resampling.LANCZOS)

    page = Image.new("RGB", (PAGE_W, PAGE_H), _rgb(palette["paper"]))
    for element in background["elements"]:
        overlay = Image.new("RGBA", (PAGE_W, PAGE_H), (0, 0, 0, 0))
        _draw_element(overlay, element, palette)
        page = Image.alpha_composite(page.convert("RGBA"), overlay).convert("RGB")
    return page


def _layout_boxes(layout: str) -> list[tuple[int, int, int, int]]:
    return {
        "single": [(250, 430, 1550, 2620)],
        "pair": [(140, 500, 840, 2550), (960, 500, 1660, 2550)],
        "two-one": [(120, 360, 820, 1480), (980, 360, 1680, 1480), (470, 1630, 1330, 2760)],
        "hero-3": [(160, 350, 1640, 1480), (180, 1640, 830, 2760), (970, 1640, 1620, 2760)],
        "grid-4": [(120, 350, 830, 1450), (970, 350, 1680, 1450), (120, 1580, 830, 2760), (970, 1580, 1680, 2760)],
        "two-column": [(130, 360, 830, 1390), (130, 1540, 830, 2740), (970, 470, 1670, 1570), (970, 1720, 1670, 2740)],
        "masonry-4": [(120, 350, 800, 1600), (120, 1740, 800, 2760), (940, 350, 1680, 1250), (940, 1390, 1680, 2760)],
        "hero-4": [(160, 330, 1640, 1460), (100, 1640, 610, 2740), (645, 1640, 1155, 2740), (1190, 1640, 1700, 2740)],
    }[layout]


def _fit_photo(image: Any, slot: tuple[int, int, int, int]) -> tuple[Any, list[int], list[int]]:
    Image, _, _, _ = _pillow()
    left, top, right, bottom = slot
    max_w = right - left - MAT_PADDING * 2
    max_h = bottom - top - MAT_PADDING * 2
    scale = min(max_w / image.width, max_h / image.height)
    width = max(1, round(image.width * scale))
    height = max(1, round(image.height * scale))
    resized = image.resize((width, height), Image.Resampling.LANCZOS)
    mat_w = width + MAT_PADDING * 2
    mat_h = height + MAT_PADDING * 2
    mat_left = left + ((right - left) - mat_w) // 2
    mat_top = top + ((bottom - top) - mat_h) // 2
    mat_box = [mat_left, mat_top, mat_left + mat_w, mat_top + mat_h]
    image_box = [mat_left + MAT_PADDING, mat_top + MAT_PADDING, mat_left + MAT_PADDING + width, mat_top + MAT_PADDING + height]
    return resized, mat_box, image_box


def _intersects(first: list[int], second: list[int]) -> bool:
    return not (first[2] <= second[0] or second[2] <= first[0] or first[3] <= second[1] or second[3] <= first[1])


def _sticker_position(anchor: str, size: tuple[int, int], mat: list[int], image: list[int], allow_overlap: bool) -> tuple[int, int]:
    width, height = size
    left, top, right, bottom = mat
    if allow_overlap:
        return {
            "top-left": (left - round(width * 0.25), top - round(height * 0.25)),
            "top-right": (right - round(width * 0.75), top - round(height * 0.25)),
            "bottom-left": (left - round(width * 0.25), bottom - round(height * 0.75)),
            "bottom-right": (right - round(width * 0.75), bottom - round(height * 0.75)),
        }[anchor]

    corner_x = left if anchor.endswith("left") else right
    corner_y = top if anchor.startswith("top") else bottom
    horizontal = left - width + 12 if anchor.endswith("left") else right - 12
    vertical = top - height + 12 if anchor.startswith("top") else bottom - 12
    candidates = [
        (horizontal, vertical),
        (corner_x if anchor.endswith("left") else corner_x - width, vertical),
        (horizontal, corner_y if anchor.startswith("top") else corner_y - height),
    ]
    for x, y in candidates:
        box = [x, y, x + width, y + height]
        if 18 <= x and 18 <= y and x + width <= PAGE_W - 18 and y + height <= PAGE_H - 18 and not _intersects(box, image):
            return x, y
    raise ValueError(f"No safe in-page sticker position for anchor {anchor}")


def compose(plan: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    Image, ImageDraw, _, _ = _pillow()
    try:
        from validate_album_plan import validate_plan
    except ImportError as exc:
        raise RuntimeError("validate_album_plan.py must be beside this script.") from exc

    errors = validate_plan(plan, require_rendered=False)
    if errors:
        raise ValueError("Plan validation failed: " + " | ".join(errors))

    output_dir.mkdir(parents=True, exist_ok=True)
    pages_dir = output_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    rendered_plan = copy.deepcopy(plan)
    photos = {item["id"]: item for item in rendered_plan["photos"]}
    rendered_pages = []

    for page_spec in rendered_plan["pages"]:
        page = _background(page_spec)
        draw = ImageDraw.Draw(page)
        placements: dict[str, dict[str, list[int]]] = {}
        slots = _layout_boxes(page_spec["layout"])
        if len(slots) != len(page_spec["photo_ids"]):
            raise ValueError(f"Layout count mismatch on page {page_spec['page']}")

        for photo_id, slot in zip(page_spec["photo_ids"], slots):
            photo_spec = photos[photo_id]
            source_path = Path(photo_spec["path"])
            if photo_spec["processing"] == "stylized-variant":
                source_path = Path(photo_spec["variant_path"])
            image = _load_rgb(source_path)
            fitted, mat_box, image_box = _fit_photo(image, slot)
            rule = page_spec["palette"]["dark"]
            draw.rectangle(mat_box, fill=page_spec["palette"]["paper"], outline=rule, width=2)
            page.paste(fitted, (image_box[0], image_box[1]))
            placements[photo_id] = {"mat_box": mat_box, "image_box": image_box}

        mat_boxes = [item["mat_box"] for item in placements.values()]
        for index, first in enumerate(mat_boxes):
            for second in mat_boxes[index + 1 :]:
                if _intersects(first, second):
                    raise ValueError(f"Photo mats overlap on page {page_spec['page']}")

        for sticker in page_spec.get("stickers", []):
            sticker_path = Path(sticker["path"])
            with Image.open(sticker_path) as source:
                asset = source.convert("RGBA")
            target_width = max(24, round(PAGE_W * float(sticker["scale"])))
            target_height = max(24, round(asset.height * target_width / asset.width))
            asset = asset.resize((target_width, target_height), Image.Resampling.LANCZOS)
            asset = asset.rotate(float(sticker["rotation"]), resample=Image.Resampling.BICUBIC, expand=True)
            target_id = sticker["target_photo_id"]
            target_spec = photos[target_id]
            allow_overlap = bool(sticker.get("allow_photo_overlap", False))
            if target_spec["subject_type"] in {"portrait", "mixed"}:
                allow_overlap = False
            target = placements[target_id]
            x, y = _sticker_position(sticker["anchor"], asset.size, target["mat_box"], target["image_box"], allow_overlap)
            sticker_box = [x, y, x + asset.width, y + asset.height]
            if target_spec["subject_type"] in {"portrait", "mixed"} and _intersects(sticker_box, target["image_box"]):
                raise ValueError(f"Sticker touches protected portrait pixels on page {page_spec['page']}")
            page.alpha_composite(asset, (x, y)) if page.mode == "RGBA" else page.paste(asset, (x, y), asset)

        page_path = pages_dir / f"page-{page_spec['page']:03d}.png"
        _atomic_save_png(page.convert("RGB"), page_path)
        page_spec["rendered_path"] = str(page_path.resolve())
        page_spec["placements"] = placements
        rendered_pages.append(str(page_path.resolve()))

    rendered_plan_path = output_dir / "album-plan-rendered.json"
    rendered_plan_path.write_text(json.dumps(rendered_plan, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "ok": True,
        "page_count": len(rendered_pages),
        "pages": rendered_pages,
        "rendered_plan": str(rendered_plan_path.resolve()),
    }


def run_self_test() -> None:
    Image, ImageDraw, _, _ = _pillow()
    palette = {"paper": "#eee9df", "dominant": "#66776f", "support": "#a8ada6", "accent": "#b97842", "dark": "#303633"}
    with tempfile.TemporaryDirectory(prefix="album-compose-") as temp_dir:
        root = Path(temp_dir)
        photos = []
        for index in range(1, 5):
            size = (1600, 1000) if index == 1 else (1000, 1400)
            path = root / f"photo-{index}.jpg"
            Image.new("RGB", size, (50 + index * 35, 80 + index * 20, 105 + index * 15)).save(path, quality=95)
            subject = "mixed" if index == 2 else "object" if index == 4 else "scenery"
            photos.append({
                "id": f"p{index:03d}", "path": str(path),
                "orientation": "landscape" if index == 1 else "portrait",
                "subject_type": subject,
                "processing": "original-only" if subject == "mixed" else "accent-assets",
                "safe_edges": ["top", "right"], "motifs": [] if subject == "mixed" else ["arch"],
                "palette": palette,
            })
        sticker_path = root / "sticker.png"
        sticker = Image.new("RGBA", (240, 180), (0, 0, 0, 0))
        ImageDraw.Draw(sticker).ellipse((20, 20, 220, 160), fill=(185, 115, 66, 255))
        sticker.save(sticker_path)
        plan = {
            "album_title": "Self Test", "volume": 1, "photos": photos,
            "pages": [{
                "page": 1, "role": "cover-page", "layout": "hero-4",
                "photo_ids": ["p001", "p002", "p003", "p004"], "palette": palette,
                "background": {"mode": "procedural", "elements": [
                    {"kind": "wash", "source_photo_id": None, "motif": "palette wash", "color_role": "support", "placement": "upper-right", "opacity": 22},
                    {"kind": "arch", "source_photo_id": "p001", "motif": "arch", "color_role": "dominant", "placement": "lower-left", "opacity": 30},
                ]},
                "stickers": [{
                    "source_photo_id": "p004", "motif": "disc", "path": str(sticker_path),
                    "target_photo_id": "p002", "anchor": "top-right", "scale": 0.07,
                    "rotation": -5, "allow_photo_overlap": False,
                }],
            }],
            "extras": [],
        }
        result = compose(plan, root / "output")
        assert result["page_count"] == 1
        with Image.open(result["pages"][0]) as rendered:
            rendered.load()
            assert rendered.size == (PAGE_W, PAGE_H)
        assert Path(result["rendered_plan"]).is_file()
        print(json.dumps({"ok": True, "tests": 4}, ensure_ascii=False))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", help="Path to album-plan.json")
    parser.add_argument("--output-dir", help="Output directory")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        run_self_test()
        return 0
    if not args.plan or not args.output_dir:
        parser.error("--plan and --output-dir are required unless --self-test is used")
    try:
        plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
        result = compose(plan, Path(args.output_dir))
    except (OSError, ValueError, RuntimeError, KeyError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
