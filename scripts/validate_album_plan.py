#!/usr/bin/env python3
"""Validate a self-contained scrapbook album plan before and after rendering."""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any


SUBJECT_TYPES = {"portrait", "mixed", "scenery", "object"}
PROCESSING_MODES = {"original-only", "accent-assets", "stylized-variant"}
ORIENTATIONS = {"portrait", "landscape", "square"}
SAFE_EDGES = {"top", "right", "bottom", "left", "none"}
PAGE_ROLES = {"cover-page", "album-page", "chapter-page", "closing-page"}
LAYOUT_COUNTS = {
    "single": {1},
    "pair": {2},
    "two-one": {3},
    "hero-3": {3},
    "grid-4": {4},
    "two-column": {4},
    "masonry-4": {4},
    "hero-4": {4},
}
PALETTE_KEYS = {"paper", "dominant", "support", "accent", "dark"}
BACKGROUND_MODES = {"procedural", "asset"}
BACKGROUND_KINDS = {"wash", "arch", "wave", "disc", "grid", "leaf", "tape", "frame"}
COLOR_ROLES = PALETTE_KEYS
PLACEMENTS = {"upper-left", "upper-right", "center-left", "center-right", "lower-left", "lower-right"}
STICKER_ANCHORS = {"top-left", "top-right", "bottom-left", "bottom-right"}
HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


def _is_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_palette(value: Any, label: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object.")
        return
    missing = sorted(PALETTE_KEYS - set(value))
    if missing:
        errors.append(f"{label} is missing: {', '.join(missing)}")
    for key in PALETTE_KEYS:
        color = value.get(key)
        if not isinstance(color, str) or not HEX_COLOR.fullmatch(color):
            errors.append(f"{label}.{key} must be a six-digit hex color.")


def _check_alpha_png(path: Path) -> str | None:
    try:
        from PIL import Image
    except ImportError:
        return None
    try:
        with Image.open(path) as image:
            rgba = image.convert("RGBA")
            width, height = rgba.size
            corners = [
                rgba.getpixel((0, 0))[3],
                rgba.getpixel((width - 1, 0))[3],
                rgba.getpixel((0, height - 1))[3],
                rgba.getpixel((width - 1, height - 1))[3],
            ]
            if any(alpha != 0 for alpha in corners):
                return "must have transparent corners"
            if rgba.getextrema()[3][1] == 0:
                return "contains no opaque sticker pixels"
    except OSError as exc:
        return str(exc)
    return None


def _expected_page_counts(photo_count: int) -> list[int] | None:
    if photo_count <= 0:
        return None
    if photo_count <= 4:
        return [photo_count]
    if photo_count == 5:
        return [3, 2]
    page_count = (photo_count + 3) // 4
    counts = [3] * page_count
    remaining = photo_count - 3 * page_count
    for index in range(remaining):
        counts[index] += 1
    return counts


def validate_plan(plan: Any, require_rendered: bool = False) -> list[str]:
    errors: list[str] = []
    if not isinstance(plan, dict):
        return ["Plan root must be a JSON object."]
    if not _is_text(plan.get("album_title")):
        errors.append("album_title must be a non-empty string.")
    volume = plan.get("volume")
    if not isinstance(volume, int) or isinstance(volume, bool) or volume < 1:
        errors.append("volume must be an integer greater than or equal to 1.")

    photos = plan.get("photos")
    if not isinstance(photos, list) or not photos:
        errors.append("photos must be a non-empty array.")
        photos = []
    if len(photos) > 24:
        errors.append("A volume may contain at most 24 unique photos.")

    photo_by_id: dict[str, dict[str, Any]] = {}
    for index, photo in enumerate(photos, start=1):
        label = f"photos[{index}]"
        if not isinstance(photo, dict):
            errors.append(f"{label} must be an object.")
            continue
        photo_id = photo.get("id")
        if not _is_text(photo_id):
            errors.append(f"{label}.id must be a non-empty string.")
            continue
        if photo_id in photo_by_id:
            errors.append(f"Duplicate photo ID: {photo_id}")
        photo_by_id[photo_id] = photo
        if not _is_text(photo.get("path")):
            errors.append(f"{label}.path must be a non-empty string.")
        if photo.get("orientation") not in ORIENTATIONS:
            errors.append(f"{label}.orientation is invalid.")
        subject_type = photo.get("subject_type")
        processing = photo.get("processing")
        if subject_type not in SUBJECT_TYPES:
            errors.append(f"{label}.subject_type is invalid.")
        if processing not in PROCESSING_MODES:
            errors.append(f"{label}.processing is invalid.")
        if subject_type in {"portrait", "mixed"} and processing != "original-only":
            errors.append(f"{label} contains a person and must use original-only.")
        if processing == "stylized-variant":
            variant_path = photo.get("variant_path")
            if not _is_text(variant_path):
                errors.append(f"{label}.variant_path is required for stylized-variant.")
            elif require_rendered and not Path(variant_path).is_file():
                errors.append(f"{label}.variant_path must exist.")
        safe_edges = photo.get("safe_edges")
        if not isinstance(safe_edges, list) or not safe_edges:
            errors.append(f"{label}.safe_edges must be a non-empty array.")
        elif any(edge not in SAFE_EDGES for edge in safe_edges):
            errors.append(f"{label}.safe_edges contains an invalid edge.")
        motifs = photo.get("motifs")
        if not isinstance(motifs, list) or any(not _is_text(item) for item in motifs):
            errors.append(f"{label}.motifs must be an array of strings.")
        _validate_palette(photo.get("palette"), f"{label}.palette", errors)

    pages = plan.get("pages")
    if not isinstance(pages, list) or not pages:
        errors.append("pages must be a non-empty array.")
        pages = []

    page_numbers: list[int] = []
    page_counts: list[int] = []
    used_photo_ids: list[str] = []
    rendered_paths: list[str] = []
    for index, page in enumerate(pages, start=1):
        label = f"pages[{index}]"
        if not isinstance(page, dict):
            errors.append(f"{label} must be an object.")
            continue
        number = page.get("page")
        if not isinstance(number, int) or isinstance(number, bool):
            errors.append(f"{label}.page must be an integer.")
        else:
            page_numbers.append(number)
        if page.get("role") not in PAGE_ROLES:
            errors.append(f"{label}.role is invalid.")
        layout = page.get("layout")
        if layout not in LAYOUT_COUNTS:
            errors.append(f"{label}.layout is invalid.")

        refs = page.get("photo_ids")
        if not isinstance(refs, list) or not refs:
            errors.append(f"{label}.photo_ids must be a non-empty array.")
            refs = []
        count = len(refs)
        page_counts.append(count)
        if count > 4:
            errors.append(f"{label} references more than four photos.")
        if layout in LAYOUT_COUNTS and count not in LAYOUT_COUNTS[layout]:
            errors.append(f"{label}.layout {layout!r} does not accept {count} photos.")
        for photo_id in refs:
            if photo_id not in photo_by_id:
                errors.append(f"{label} references unknown photo ID {photo_id!r}.")
            elif isinstance(photo_id, str):
                used_photo_ids.append(photo_id)

        _validate_palette(page.get("palette"), f"{label}.palette", errors)
        background = page.get("background")
        if not isinstance(background, dict):
            errors.append(f"{label}.background must be an object.")
            background = {}
        mode = background.get("mode")
        if mode not in BACKGROUND_MODES:
            errors.append(f"{label}.background.mode is invalid.")
        elements = background.get("elements")
        if not isinstance(elements, list) or not 2 <= len(elements) <= 4:
            errors.append(f"{label}.background.elements must contain 2-4 items.")
            elements = []
        for element_index, element in enumerate(elements, start=1):
            element_label = f"{label}.background.elements[{element_index}]"
            if not isinstance(element, dict):
                errors.append(f"{element_label} must be an object.")
                continue
            kind = element.get("kind")
            if kind not in BACKGROUND_KINDS:
                errors.append(f"{element_label}.kind is invalid.")
            source_id = element.get("source_photo_id")
            if source_id is not None:
                source = photo_by_id.get(source_id)
                if source is None:
                    errors.append(f"{element_label} references unknown source photo.")
                elif source.get("subject_type") not in {"scenery", "object"}:
                    errors.append(f"{element_label} motif source must be scenery or object.")
            elif kind not in {"wash", "tape", "frame"}:
                errors.append(f"{element_label} requires a scenery/object source photo.")
            if not _is_text(element.get("motif")):
                errors.append(f"{element_label}.motif must be a non-empty string.")
            if element.get("color_role") not in COLOR_ROLES:
                errors.append(f"{element_label}.color_role is invalid.")
            if element.get("placement") not in PLACEMENTS:
                errors.append(f"{element_label}.placement is invalid.")
            opacity = element.get("opacity")
            if not isinstance(opacity, int) or isinstance(opacity, bool) or not 5 <= opacity <= 80:
                errors.append(f"{element_label}.opacity must be an integer from 5 to 80.")
        if mode == "asset" and require_rendered:
            background_path = background.get("rendered_path")
            if not _is_text(background_path) or not Path(background_path).is_file():
                errors.append(f"{label}.background.rendered_path must exist for asset mode.")

        stickers = page.get("stickers", [])
        if not isinstance(stickers, list) or len(stickers) > 5:
            errors.append(f"{label}.stickers must be an array with at most five items.")
            stickers = []
        for sticker_index, sticker in enumerate(stickers, start=1):
            sticker_label = f"{label}.stickers[{sticker_index}]"
            if not isinstance(sticker, dict):
                errors.append(f"{sticker_label} must be an object.")
                continue
            source = photo_by_id.get(sticker.get("source_photo_id"))
            if source is None or source.get("subject_type") not in {"scenery", "object"}:
                errors.append(f"{sticker_label} source must be scenery or object.")
            if not _is_text(sticker.get("motif")):
                errors.append(f"{sticker_label}.motif must be a non-empty string.")
            target_id = sticker.get("target_photo_id")
            if target_id not in refs:
                errors.append(f"{sticker_label}.target_photo_id must be on the same page.")
            if sticker.get("anchor") not in STICKER_ANCHORS:
                errors.append(f"{sticker_label}.anchor is invalid.")
            scale = sticker.get("scale")
            if not isinstance(scale, (int, float)) or isinstance(scale, bool) or not 0.03 <= scale <= 0.15:
                errors.append(f"{sticker_label}.scale must be between 0.03 and 0.15.")
            rotation = sticker.get("rotation")
            if not isinstance(rotation, (int, float)) or isinstance(rotation, bool) or not -30 <= rotation <= 30:
                errors.append(f"{sticker_label}.rotation must be between -30 and 30.")
            overlap = sticker.get("allow_photo_overlap", False)
            if not isinstance(overlap, bool):
                errors.append(f"{sticker_label}.allow_photo_overlap must be boolean.")
            target = photo_by_id.get(target_id)
            if target and target.get("subject_type") in {"portrait", "mixed"} and overlap:
                errors.append(f"{sticker_label} may not overlap portrait or mixed photo pixels.")
            if require_rendered:
                sticker_path = sticker.get("path")
                if not _is_text(sticker_path) or not Path(sticker_path).is_file():
                    errors.append(f"{sticker_label}.path must exist.")

        if require_rendered:
            rendered = page.get("rendered_path")
            if not _is_text(rendered) or not Path(rendered).is_file():
                errors.append(f"{label}.rendered_path must exist.")
            else:
                rendered_paths.append(rendered)

    if page_numbers and page_numbers != list(range(1, len(pages) + 1)):
        errors.append("Page numbers must be sequential and match array order.")
    if pages and isinstance(pages[0], dict) and pages[0].get("role") != "cover-page":
        errors.append("The first page must use role 'cover-page'.")
    if len(pages) > 1 and isinstance(pages[-1], dict) and pages[-1].get("role") != "closing-page":
        errors.append("The last page must use role 'closing-page'.")

    expected_counts = _expected_page_counts(len(photo_by_id))
    if expected_counts and sorted(page_counts, reverse=True) != sorted(expected_counts, reverse=True):
        errors.append(f"Page photo counts must balance as {expected_counts}.")
    if len(used_photo_ids) != len(set(used_photo_ids)):
        errors.append("Photos may not repeat across pages in the default compact album.")
    unused = sorted(set(photo_by_id) - set(used_photo_ids))
    if unused:
        errors.append(f"Photos not used in the plan: {', '.join(unused)}")
    if require_rendered and len(rendered_paths) != len(set(rendered_paths)):
        errors.append("Every page must have a distinct rendered_path.")

    extras = plan.get("extras", [])
    if not isinstance(extras, list):
        errors.append("extras must be an array.")
        extras = []
    for index, extra in enumerate(extras, start=1):
        label = f"extras[{index}]"
        if not isinstance(extra, dict) or extra.get("role") != "transparent-stickers":
            errors.append(f"{label} must be a transparent-stickers object.")
            continue
        source_ids = extra.get("source_photo_ids")
        if not isinstance(source_ids, list) or len(source_ids) < 1:
            errors.append(f"{label}.source_photo_ids must be a non-empty array.")
            source_ids = []
        for source_id in source_ids:
            source = photo_by_id.get(source_id)
            if source is None or source.get("subject_type") not in {"scenery", "object"}:
                errors.append(f"{label} sources must be scenery or object photos.")
        if str(extra.get("format", "")).lower() != "png" or extra.get("alpha_required") is not True:
            errors.append(f"{label} must require a transparent PNG.")
        if require_rendered:
            rendered = extra.get("rendered_path")
            if not _is_text(rendered) or not Path(rendered).is_file():
                errors.append(f"{label}.rendered_path must exist.")
            else:
                alpha_error = _check_alpha_png(Path(rendered))
                if alpha_error:
                    errors.append(f"{label} {alpha_error}.")

    return errors


def _valid_fixture() -> dict[str, Any]:
    palette = {"paper": "#eee9df", "dominant": "#66776f", "support": "#a8ada6", "accent": "#b97842", "dark": "#303633"}
    photos = []
    for index in range(1, 7):
        subject = "portrait" if index == 2 else "scenery" if index % 2 else "object"
        photos.append({
            "id": f"p{index:03d}",
            "path": f"/photos/{index}.jpg",
            "orientation": "landscape" if index in {1, 4} else "portrait",
            "subject_type": subject,
            "processing": "original-only" if subject == "portrait" else "accent-assets",
            "safe_edges": ["top", "right"],
            "motifs": [] if subject == "portrait" else ["arch"],
            "palette": palette,
        })
    def page(number: int, role: str, refs: list[str], source: str) -> dict[str, Any]:
        return {
            "page": number,
            "role": role,
            "layout": "hero-3",
            "photo_ids": refs,
            "palette": palette,
            "background": {
                "mode": "procedural",
                "elements": [
                    {"kind": "wash", "source_photo_id": None, "motif": "palette wash", "color_role": "support", "placement": "upper-right", "opacity": 24},
                    {"kind": "arch", "source_photo_id": source, "motif": "arch", "color_role": "dominant", "placement": "lower-left", "opacity": 32},
                ],
            },
            "stickers": [],
        }
    return {
        "album_title": "Self Test",
        "volume": 1,
        "photos": photos,
        "pages": [
            page(1, "cover-page", ["p001", "p002", "p003"], "p001"),
            page(2, "closing-page", ["p004", "p005", "p006"], "p004"),
        ],
        "extras": [],
    }


def run_self_test() -> None:
    valid = _valid_fixture()
    assert not validate_plan(valid), validate_plan(valid)

    portrait_edit = copy.deepcopy(valid)
    portrait_edit["photos"][1]["processing"] = "stylized-variant"
    assert any("must use original-only" in item for item in validate_plan(portrait_edit))

    human_sticker = copy.deepcopy(valid)
    human_sticker["pages"][0]["stickers"] = [{
        "source_photo_id": "p002", "motif": "person", "target_photo_id": "p001",
        "anchor": "top-right", "scale": 0.08, "rotation": 0, "allow_photo_overlap": False,
    }]
    assert any("source must be scenery or object" in item for item in validate_plan(human_sticker))

    flat = copy.deepcopy(valid)
    flat["pages"][0]["background"]["elements"] = []
    assert any("2-4" in item for item in validate_plan(flat))

    duplicate = copy.deepcopy(valid)
    duplicate["pages"][1]["photo_ids"][0] = "p001"
    assert any("may not repeat" in item for item in validate_plan(duplicate))

    print(json.dumps({"ok": True, "tests": 5}, ensure_ascii=False))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", nargs="?", help="Path to album-plan.json")
    parser.add_argument("--require-rendered", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        run_self_test()
        return 0
    if not args.plan:
        parser.error("plan is required unless --self-test is used")
    try:
        plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "errors": [str(exc)]}, ensure_ascii=False))
        return 2
    errors = validate_plan(plan, require_rendered=args.require_rendered)
    print(json.dumps({
        "ok": not errors,
        "errors": errors,
        "page_count": len(plan.get("pages", [])) if isinstance(plan, dict) else 0,
        "photo_count": len(plan.get("photos", [])) if isinstance(plan, dict) else 0,
    }, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
