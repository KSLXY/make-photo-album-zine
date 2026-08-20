# Album blueprint

## Contents

- Master format
- Photo inventory
- Grouping and page balance
- Layout selection
- Album-plan schema
- Rendering rules

## Master format

- Canvas: portrait 3:5, preferably 1800 x 3000 pixels.
- Photo treatment: contain, never crop; preserve complete image content and aspect ratio.
- Page density: 3-4 photos by default. Keep the first and last pages at the same density instead of adding a single-photo cover.
- Photo frame separation: at least 48 pixels on an 1800-pixel-wide page.
- Quiet area: reserve 8-14% of the page for breathing room, title microtype, and edge decoration.
- Decoration: stickers may touch a mat edge but may not cover protected photo pixels.

## Photo inventory

Record every photo before grouping:

| Field | Allowed values or guidance |
|---|---|
| `id` | Stable upload-order ID such as `p001` |
| `path` | Absolute local path |
| `orientation` | `portrait`, `landscape`, `square` |
| `subject_type` | `portrait`, `mixed`, `scenery`, `object` |
| `processing` | See the matrix below |
| `safe_edges` | Any of `top`, `right`, `bottom`, `left`; use `none` when uncertain |
| `motifs` | 0-6 visible non-human nouns such as `arch`, `leaf`, `book`, `cup`, `wave` |
| `palette` | Deterministic output from `extract_palette.py` |

Processing matrix:

| Subject type | Allowed processing |
|---|---|
| `portrait` | `original-only` |
| `mixed` | `original-only` |
| `scenery` | `original-only`, `accent-assets`, `stylized-variant` |
| `object` | `original-only`, `accent-assets`, `stylized-variant` |

If any recognizable person appears and classification is uncertain, use `mixed` and `original-only`.

## Grouping and page balance

Group in this order:

1. dominant color family and light temperature;
2. contrast and emotional temperature;
3. scene continuity;
4. orientation balance.

Keep same-tone photos together, but move one visually compatible photo to an adjacent group when necessary to avoid a weak one-photo remainder.

Use these page counts:

- 1-2 photos: one exceptional page using the available count.
- 3 photos: one 3-photo page.
- 4 photos: one 4-photo page.
- 5 photos: one 3-photo page and one 2-photo page; this is the only unavoidable compact-album exception.
- 6 or more photos: distribute into pages of 3-4 photos. Use as many 4-photo pages as possible without leaving fewer than 3 for the final page.

Examples: 6=`3+3`, 7=`4+3`, 8=`4+4`, 9=`3+3+3`, 10=`4+3+3`, 11=`4+4+3`, 12=`4+4+4`.

## Layout selection

Choose one layout per page. Photo frames never overlap.

| Layout | Count | Best use |
|---|---:|---|
| `single` | 1 | Only when the entire volume has one photo |
| `pair` | 2 | Two-photo input or the 5-photo remainder |
| `two-one` | 3 | Three portrait or square photos |
| `hero-3` | 3 | One landscape hero plus two supporting photos |
| `grid-4` | 4 | Four similarly oriented photos |
| `two-column` | 4 | Four portrait/square photos with varied visual weight |
| `masonry-4` | 4 | Mixed portrait and square photos |
| `hero-4` | 4 | One landscape hero plus three supporting photos |

Selection rules:

- Use `hero-3` or `hero-4` only when one landscape image is clearly stronger.
- Use at most one hero per page.
- Prefer `grid-4` for a calm, evenly weighted series.
- Prefer `two-column` when two visual pairs exist.
- Prefer `masonry-4` when aspect ratios differ but no single photo should dominate.
- Use `two-one` for a quiet final page or a three-image narrative.

## Album-plan schema

Create one JSON object per volume. Omit `rendered_path` fields before rendering.

```json
{
  "album_title": "光影日常",
  "volume": 1,
  "photos": [
    {
      "id": "p001",
      "path": "/absolute/path/photo.jpg",
      "orientation": "portrait",
      "subject_type": "mixed",
      "processing": "original-only",
      "safe_edges": ["top", "right"],
      "motifs": ["bridge", "water"],
      "palette": {
        "paper": "#eee9df",
        "dominant": "#6c7770",
        "support": "#a8ada6",
        "accent": "#b97842",
        "dark": "#303633"
      }
    }
  ],
  "pages": [
    {
      "page": 1,
      "role": "cover-page",
      "layout": "two-one",
      "photo_ids": ["p001", "p002", "p003"],
      "palette": {
        "paper": "#eee9df",
        "dominant": "#6c7770",
        "support": "#a8ada6",
        "accent": "#b97842",
        "dark": "#303633"
      },
      "background": {
        "mode": "procedural",
        "elements": [
          {
            "kind": "wash",
            "source_photo_id": "p001",
            "motif": "water",
            "color_role": "support",
            "placement": "upper-right",
            "opacity": 30
          },
          {
            "kind": "arch",
            "source_photo_id": "p001",
            "motif": "bridge",
            "color_role": "dominant",
            "placement": "lower-left",
            "opacity": 38
          }
        ]
      },
      "stickers": [
        {
          "source_photo_id": "p002",
          "motif": "leaf",
          "path": "/absolute/path/leaf-sticker.png",
          "target_photo_id": "p001",
          "anchor": "top-right",
          "scale": 0.08,
          "rotation": -6,
          "allow_photo_overlap": false
        }
      ],
      "rendered_path": "/absolute/path/page-001.png"
    }
  ],
  "extras": [
    {
      "role": "transparent-stickers",
      "source_photo_ids": ["p002"],
      "format": "png",
      "alpha_required": true,
      "rendered_path": "/absolute/path/stickers-transparent.png"
    }
  ]
}
```

Allowed page roles: `cover-page`, `album-page`, `chapter-page`, `closing-page`.

Allowed procedural background kinds: `wash`, `arch`, `wave`, `disc`, `grid`, `leaf`, `tape`, `frame`.

Allowed placements: `upper-left`, `upper-right`, `center-left`, `center-right`, `lower-left`, `lower-right`.

Sticker anchors are relative to the target photo mat: `top-left`, `top-right`, `bottom-left`, `bottom-right`.

## Rendering rules

- `background.mode: procedural` uses page palette and elements drawn by the compositor.
- `background.mode: asset` requires a 3:5 `background.rendered_path`; it must contain no people, text, or reconstructed photos.
- Use 2-4 background elements. At least one must use `support` or `accent`; do not render a single flat fill.
- `wash`, `tape`, and `frame` may omit `source_photo_id` because they use only the extracted page palette. Every other motif kind requires a `scenery` or `object` source photo.
- Use 0-5 stickers. A sticker source must be `scenery` or `object`.
- Default `allow_photo_overlap` to `false`. For `portrait` and `mixed` targets, it must remain `false`.
- When sticker placement is unsafe, remove the sticker rather than moving it over the subject.
- After composition, add `rendered_path` to every page and any delivered extra, then validate with `--require-rendered`.
