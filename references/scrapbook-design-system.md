# Scrapbook design system

Use this original, self-contained design system for the whole album. Do not invoke or imitate a named external photo skill.

## Page character

- Aim for a tactile personal scrapbook: quiet paper, source-related color washes, simple cut-paper echoes, small transparent stickers, and clearly separated photos.
- Keep photographs primary. Background and stickers support the memory instead of becoming the subject.
- Keep 55-70% of the page visually calm. Use asymmetry and varied scale, but avoid chaotic overlap.
- Repeat a small page number, mat rule, or tape treatment across the volume for continuity.

## Palette construction

Use the local palette extractor rather than guessing colors.

- `paper`: a light neutral tinted toward the page photos' dominant color.
- `dominant`: the strongest recurring source color.
- `support`: a quieter neighboring or neutral source color.
- `accent`: one small higher-saturation source color; omit it when none is truthful.
- `dark`: a chromatic structural dark for thin rules and microtype.

Use `paper` over most of the page. Use `dominant` and `support` in translucent background elements. Limit `accent` to roughly 2-6% of the page. Do not apply one identical paper color to every page when page groups differ.

## Layered background recipe

Build 2-4 controlled layers:

1. tinted paper field from `paper`;
2. one broad low-opacity `wash` from `support` or `dominant`;
3. one or two motif echoes derived from visible scenery or objects;
4. optional tape, frame, or tiny accent mark.

When using a generated background asset, create the background only. Require a 3:5 empty scrapbook page, sampled palette, 2-4 source-derived non-human motifs, open photo zones, no people, no photographs, no text, no logos, and no watermark.

## Motif translation

Translate visible elements into simple background grammar:

| Visible source element | Suitable echo |
|---|---|
| bridge, doorway, wheel | arch or concentric line |
| window, shelf, facade | grid or thin frame |
| river, shoreline, cloud | wave or translucent wash |
| tree, vine, flower | sparse leaf or branch gesture |
| book, ticket, paper | tab, label, or torn tape strip |
| plate, cup, record, lamp | disc or partial ring |
| road, railing, steps | stripe, ladder, or repeated short rule |

Do not add a motif that is absent from the source set. Reduce literal detail; keep only the recognizable shape grammar.

## Photo mats

- Preserve the complete source photo and aspect ratio.
- Use a 12-24 pixel paper mat and a 1-3 pixel rule sampled from `dark` or `dominant`.
- Keep at least 48 pixels between photo mats on an 1800-pixel-wide page.
- Never overlap photo frames. Only stickers and paper tape may touch a mat edge.
- For a portrait or mixed photo, place every decoration outside the actual image pixels.

## Sticker system

- Derive stickers only from scenery and objects: leaves, arches, cups, books, food, signs without readable text, clouds, water shapes, lamps, records, or architectural details.
- Never turn a face, body, hairstyle, clothing silhouette, name, logo, or private metadata into a sticker.
- Use 0-5 stickers per page; 2-4 is the normal range when qualified motifs exist.
- Keep most stickers at 4-9% of page width and one optional hero sticker at no more than 12%.
- Use a warm or cool paper-cut border related to the page paper. Keep Alpha transparency real.
- Place stickers beside a photo corner or across only the outer mat edge. On portrait and mixed photos, overlap actual image pixels by 0%.
- Vary size and rotation slightly. Reuse one motif at most twice in a volume.

For a generated sticker sheet, request separated transparent motifs in two or three relaxed rows, no people, no text, no card background, no checkerboard, and no cast shadow beyond a subtle flat paper edge.

## Scene and object variants

Default to keeping the original scenery/object photo and generating only supporting assets. Create a stylized photo variant only when the user asks for stronger treatment or the plan explicitly sets `stylized-variant`.

When making a variant:

- preserve landmark silhouette, object geometry, lighting direction, and 3-5 identity anchors;
- simplify incidental detail instead of adding new content;
- never introduce a person;
- label the result as stylized and keep the original available for comparison;
- use the variant only as a scenery/object insert, never as evidence of an unchanged photograph.

## Rejection rules

Reject and regenerate any asset containing a new person, altered portrait, pseudo-text, signature, watermark, invented location/date, unrelated decorative flowers, generic travel icons, excessive stickers, muddy color, or a background that competes with the photos.
