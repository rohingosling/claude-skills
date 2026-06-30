---
name: ascii-memory-map
description: Render an ASCII box-drawing memory map (an address-space layout diagram) from a JSON description. Use whenever a response needs a memory map, memory layout, address map, or address-space diagram for ANY architecture (Commodore VIC-20/C64, x86 real-mode/segmented, ARM/MCU flash+SRAM, flat 32/64-bit, etc.). Separates the map's DATA from its RENDERING and offloads all box drawing, column alignment, address formatting, and size-proportional block heights to a deterministic Python renderer, so the model only authors compact JSON.
disable-model-invocation: false
---

Render an ASCII memory map using the Python script at `${CLAUDE_SKILL_DIR}/scripts/render_ascii_memory_map.py`.

Author the map as JSON (the *data*), choose presentation flags (the *rendering*), run the script, and paste its output into a fenced code block. Let the script do all box drawing, alignment, address formatting, and height scaling — do not hand-draw memory maps.

## Positioning rules (the text-placement taxonomy)

Every piece of text has exactly one home, decided by what it refers to:

| Class | What it is | Where it goes |
|-------|------------|---------------|
| **Address** | A hex/decimal boundary coordinate | Left gutter, on the divider that *opens* the block (its low-address edge) |
| **Label** | The block's short name | Inside the box, first body row |
| **Description** | Optional elaboration (extent, contents) | Inside the box, further body rows |
| **Comment / note** | Extrinsic annotation — register writes, bit patterns, caveats, consequences | Right of the box, anchored to the first body row with an arrow; continuations align beneath, no arrow |

Decisive test: text that **names or describes the contents** of a span is intrinsic → goes **inside** (label/description); text that **says something about** the span (a value, a constraint, a cross-reference) is extrinsic → goes **outside** (comment). A bare boundary coordinate goes in the **gutter**. Divider and border lines carry only the address — never a label or a comment. The renderer enforces all of this.

## Instructions

1. Construct a JSON object describing the memory map (schema below). Store addresses as numeric/hex strings — the renderer formats them for display, so the same data can be shown as `$0400`, `0x0400`, `0400h`, `0040:0000`, or `01024` by changing one flag.

2. Write the JSON to a temporary file in the current project's working directory (e.g. `memmap.json`).

3. Run the renderer (use `python3` on macOS/Linux, `python` on Windows):
   ```
   python3 "${CLAUDE_SKILL_DIR}/scripts/render_ascii_memory_map.py" memmap.json [flags]
   ```
   Defaults can also be set inside the JSON in a `"render": { ... }` object; CLI flags override the JSON, which overrides the built-in defaults.

4. Copy the output into the target markdown inside a fenced code block.

5. Delete the temporary JSON file.

## JSON schema

Top-level keys:

| Key | Type | Meaning |
|-----|------|---------|
| `title` | string | Optional heading printed above the map |
| `render` | object | Optional default values for any flag below (underscore_case keys, e.g. `"address_format": "c"`) |
| `blocks` | array | The memory regions (required) |

Each block:

| Field | Type | Meaning |
|-------|------|---------|
| `start` | int or string | Start address (required). Strings accept `$XXXX`, `0xXXXX`, `XXXXh`, `SSSS:OOOO`, or a bare numeral (hex by default) |
| `end` | int or string | Inclusive end address (last byte). Optional — if omitted, inferred from the next block's `start` |
| `size` | int or string | Alternative to `end`; accepts `2K`, `0x800`, `4096`, `64KB` |
| `label` | string | The region name (inside the box) |
| `description` | string or array | Extra inside-the-box line(s) |
| `comments` | string or array | Outside-the-box note(s); the first is arrow-anchored, the rest align beneath |
| `rows` | int | Force this block's body height (overrides scaling) |

## Parameters

| Flag | Default | Purpose |
|------|---------|---------|
| `--address-format` | `commodore` | `commodore` (`$0400`), `c` (`0x0400`), `intel` (`0400h`), `plain` (`0400`), `segmented` (`0040:0000`), `decimal`, `decimal-padded` |
| `--address-width` | auto | Digit count (4 = 16-bit, 8 = 32-bit…); auto-sized from the largest address if omitted |
| `--input-radix` | `hex` | How to read bare numeric *strings* in the JSON (`hex` / `decimal`); integers are always decimal |
| `--hex-case` | `upper` | `upper` / `lower` hex digits |
| `--origin` | `top` | `top` = low address at top (addresses increase downward); `bottom` = low address at bottom |
| `--scale` | `on` | `on` / `off` — size-proportional block heights |
| `--scale-mode` | `log` | `log` / `linear` / `sqrt` taper |
| `--min-rows` / `--max-rows` | `1` / `6` | Clamp for scaled block heights |
| `--style` | `unicode` | `unicode` / `heavy` / `double` / `ascii` (`+ - |` for non-Unicode terminals) |
| `--width` | `auto` | Interior box width: `auto` (longest label) or an integer |
| `--comment-arrow` | `◄─` | Outside-note connector (`<-` in `ascii` style) |
| `--no-comments` | off | Suppress all outside notes |
| `--show-size` | off | Append each region's computed size inside its box |
| `--show-end` | off | Show the end address on the closing boundary |
| `--show-gaps` | off | Draw unmapped ranges between blocks as their own gap blocks |
| `--gap-label` | `· · ·` | Label used for auto-generated gap blocks |
| `--paragraph` | `16` | Bytes per segment for `segmented` addresses |
| `--title` | — | Override the JSON `title` |

## Height scaling

With `--scale on` (default), a block's body height is `max( rows_needed_for_text, clamp( round(min_rows + f(size)·(max_rows−min_rows)), min_rows, max_rows ) )`, where `f` is a log/linear/sqrt normalisation of the block's size between the smallest and largest sized blocks. The log taper means one very large region is only a few rows taller than its neighbours — a visual cue to relative size, not a to-scale drawing. Tiny blocks stay readable at `min_rows`; text always fits regardless of scaling. Sizes are taken from `end`/`size`, or inferred from the next block's `start`.

## Example

JSON (`memmap.json`):

```json
{
  "title": "C64 — VIC bank 0 ($0000-$3FFF)",
  "blocks": [
    { "start": "$0000", "end": "$03FF", "label": "zero page / stack / system",
      "comments": ["$0001 CHAREN: bit 2 = 0 → char ROM at $D000"] },
    { "start": "$0400", "end": "$07FF", "label": "screen RAM (video matrix)",
      "comments": ["matrix base; $D018 bits 4-7 = %0001"] },
    { "start": "$3800", "end": "$3FFF", "label": "Westminster charset (2 KB)",
      "description": ["ROM copy + overlaid glyphs"],
      "comments": ["char base; $D018 bits 1-3 = %111 → $D018 = $1E"] }
  ]
}
```

Command:

```
python3 "${CLAUDE_SKILL_DIR}/scripts/render_ascii_memory_map.py" memmap.json --scale off
```

Output:

```
C64 — VIC bank 0 ($0000-$3FFF)

 $0000  ┌────────────────────────────┐
        │ zero page / stack / system │ ◄─ $0001 CHAREN: bit 2 = 0 → char ROM at $D000
 $0400  ├────────────────────────────┤
        │ screen RAM (video matrix)  │ ◄─ matrix base; $D018 bits 4-7 = %0001
 $3800  ├────────────────────────────┤
        │ Westminster charset (2 KB) │ ◄─ char base; $D018 bits 1-3 = %111 → $D018 = $1E
        │ ROM copy + overlaid glyphs │
        └────────────────────────────┘
```

A ready-to-run example is bundled at `${CLAUDE_SKILL_DIR}/examples/c64-bank0.json`.

## User argument

$ARGUMENTS
