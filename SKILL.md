---
name: make-photo-album-zine
description: Build complete scrapbook-style photo albums from uploaded photos with color grouping, adaptive 3-4-photo layouts, source-derived layered backgrounds, edge stickers, page PNGs, and PDF assembly. Preserve portraits and mixed people photos as original inserts by default; only scenery and object photos may be stylized. Use for 整册相册, 照片集, 手帐相册, photo books, scrapbook albums, zine albums, automatic album layout, or coordinated album generation without directing every page.
---

# Make Photo Album Zine

Create the finished album, not only a plan. Keep this workflow self-contained: do not invoke, import, or require another photo-style skill.

## Core behavior

- Preserve every accepted source photo and use it at least once.
- Classify photos as `portrait`, `mixed`, `scenery`, or `object`. When uncertain whether a recognizable person is present, use `mixed`.
- Keep `portrait` and `mixed` photos as original, uncropped inserts. Do not retouch, redraw, beautify, reconstruct, relight, replace their backgrounds, or send them to image generation as edit references.
- Allow `scenery` and `object` photos to use `original-only`, `accent-assets`, or `stylized-variant`. Default to `accent-assets`: retain the original photo and derive only background motifs or stickers from non-human content.
- If the user requests no photo processing, set every photo to `original-only`. Continue only with deterministic layout, local palette extraction, and non-photographic paper decoration.
- Use built-in image generation only for background-only assets, transparent stickers, or optional variants sourced from `scenery` and `object` photos. Never generate a complete page that contains a source portrait; composite original people photos afterward.

## Input and output contracts

- Require at least one user-supplied photo. Treat photos and metadata as private.
- Use reliable EXIF capture time when available; otherwise preserve upload order. Never invent chronology, place, date, names, quotations, or events.
- Use a 3:5 portrait page. Default to 3-4 photos per page, including the first and last pages. For 1-2 total photos, use the available count; split more than 24 unique photos into consistent numbered volumes.
- Preserve photo aspect ratios and complete image content. Resize to fit; do not crop or distort.
- Return one PDF per volume, every page as PNG, and a brief page/group list. Return a transparent sticker sheet only when at least three truthful scenery/object motifs are available or the user requests one.
- Do not create a ZIP unless requested.

## Required resources and tools

1. Read `references/album-blueprint.md` before grouping and planning.
2. Read `references/scrapbook-design-system.md` before creating backgrounds or stickers.
3. Run `scripts/extract_palette.py` to obtain deterministic color candidates.
4. Run `scripts/validate_album_plan.py` before rendering and again with `--require-rendered` before PDF assembly.
5. Use `scripts/compose_album_pages.py` to place original photos, generated backgrounds, and optional stickers without overlap.
6. Use `scripts/assemble_album.py` to create the ordered PDF.
7. Follow the PDF workflow: mark the artifact operation once, render the final PDF, and visually inspect every page.

## Workflow

### 1. Inventory and protect

- Assign stable IDs in upload order: `p001`, `p002`, and so on.
- Record orientation, subject type, scene/object motifs, focal area, quiet edges, reliable metadata, and processing mode.
- For `portrait` and `mixed`, record `processing: original-only` and one or more `safe_edges` for decoration. If safe edges cannot be established, place decoration outside the photo frame.
- Mark hero candidates by atmosphere and composition, not by ease of processing.

### 2. Extract and merge palettes

Run:

```bash
python3 scripts/extract_palette.py PHOTO... --output photo-palettes.json
```

- Group first by dominant color, light temperature, and contrast; use scene continuity as the secondary rule.
- Merge each page's photo palettes into one `paper`, `dominant`, `support`, `accent`, and `dark` set.
- Keep backgrounds related to the photos but clearly lighter or calmer than them. Do not use one flat color across the entire volume.

### 3. Plan pages

- Balance 3-4 photos per page before choosing layouts. Do not create a single-photo cover when the set supports a 3-4-photo first page.
- Choose layouts from the blueprint according to count, orientation, and visual weight.
- Use one clear hero at most. Keep photo frames separate and reserve 8-14% page area for breathing room and decoration.
- Add 2-4 background elements per page from visible non-human motifs and sampled colors. Use a mix of paper field, translucent wash, and one or two motif echoes.
- Add 0-5 stickers per page. Derive them only from scenery or objects. Place them beside frames or across the outer mat edge; never cover a face, body, landmark identity, or essential text.
- Create `album-plan.json` with the schema in `references/album-blueprint.md`, then validate it.

### 4. Create assets

- Generate background-only assets at 3:5 when procedural elements are insufficient. Ask for no people, no text, no logos, and no complete photo reconstruction.
- Generate one transparent sticker sheet per volume when qualified motifs exist. Keep motifs separated, source-faithful, and free of people, faces, names, and incidental text.
- Keep generated assets subordinate. Photographs remain the album's primary content.

### 5. Composite deterministically

Run:

```bash
python3 scripts/compose_album_pages.py --plan album-plan.json --output-dir output
```

Use the returned rendered plan for final validation. The compositor must place original people photos from their source files, preserve aspect ratios, and keep frames non-overlapping. Generated stickers may touch only the outer mat edge unless the plan explicitly marks a scenery/object image edge as safe.

### 6. Assemble and inspect

Immediately before PDF creation, mark the PDF artifact operation once, then run:

```bash
python3 scripts/assemble_album.py --plan output/album-plan-rendered.json --output output/album.pdf
```

Render the PDF with Poppler and inspect every page for photo integrity, order, clipping, unintended overlap, palette mismatch, damaged text, unsafe sticker placement, blank pages, and abrupt visual changes. Rebuild after any fix.

## Quality gate

Do not deliver until all checks pass:

- every source photo appears at least once and unexplained duplication is absent;
- each page uses the planned 3-4 photos unless the entire input contains fewer than three;
- every `portrait` and `mixed` photo remains `original-only` and visually unchanged apart from fit-to-page resizing;
- scenery/object processing never introduces people or alters a person in a mixed scene;
- page backgrounds use source-derived palettes plus 2-4 controlled layers, not a single unrelated flat fill;
- stickers come from visible scenery/object motifs and remain outside protected subject areas;
- photos do not overlap, crop, stretch, or hide behind decoration;
- page order and PDF page count match the rendered plan;
- the latest PDF render has no clipping, corruption, missing assets, or unreadable text.

## Delivery

Lead with the PDF, then page PNGs and any transparent sticker sheet. State the source photo count, volume count, page count, grouping logic, and which scenery/object assets were stylized. Explicitly state that portraits were preserved as original inserts.
