# g-render-ascii-memory-map

![Claude Code](https://img.shields.io/badge/Claude_Code-plugin-D97757?style=flat&logo=claude&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=flat&logo=python&logoColor=white)
![Dependencies](https://img.shields.io/badge/dependencies-none-3DA639?style=flat&logo=python&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-3DA639?style=flat&logo=opensourceinitiative&logoColor=white)

Render a clean **ASCII memory map** — an address-space layout diagram — from a simple JSON description, ready to
paste into a markdown fenced code block. Works for **any** architecture: Commodore VIC-20/C64, x86 real-mode /
segmented, ARM/MCU flash + SRAM, or flat 32/64-bit. The skill separates the map's **data** (blocks, labels, numeric
addresses) from its **rendering** (address format, box style, height scaling, origin direction) and offloads every
deterministic layout chore — box drawing, column alignment, address formatting, and size-proportional block heights —
to the renderer, so you only author compact JSON.

Packaged as a **Claude Code plugin** (an Agent Skill) wrapping a dependency-free Python script.

## Install

```text
/plugin marketplace add rohingosling/claude-skills
/plugin install g-render-ascii-memory-map@rohingosling-skills
/reload-plugins
```

## Usage

Invoke the skill in Claude Code — `/g-render-ascii-memory-map:ascii-memory-map` — or run the script directly against
a JSON file:

```text
python3 scripts/render_ascii_memory_map.py memmap.json --scale off
```

(Use `python` instead of `python3` on Windows.)

## JSON shape

A map is a `"blocks"` array; each block needs a `"start"` address (an integer or a string such as `"$0400"`,
`"0x0400"`, `"0400h"`, `"0040:0000"`, or a bare numeral). Give an `"end"` or a `"size"`, or let it be inferred from
the next block's `start`. `"label"` and `"description"` are drawn **inside** the box; `"comments"` are drawn **to the
right**, arrow-anchored. An optional top-level `"title"` and `"render"` block set defaults.

```json
{
    "title": "C64 — VIC bank 0 ($0000-$3FFF)",
    "blocks": [
        { "start": "$0000", "end": "$03FF", "label": "zero page / stack / system",
          "comments": [ "$0001 CHAREN: bit 2 = 0 → char ROM at $D000" ] },
        { "start": "$0400", "end": "$07FF", "label": "screen RAM (video matrix)" },
        { "start": "$3800", "end": "$3FFF", "label": "Westminster charset (2 KB)",
          "description": [ "ROM copy + overlaid glyphs" ] }
    ]
}
```

```text
C64 — VIC bank 0 ($0000-$3FFF)

 $0000  ┌────────────────────────────┐
        │ zero page / stack / system │ ◄─ $0001 CHAREN: bit 2 = 0 → char ROM at $D000
 $0400  ├────────────────────────────┤
        │ screen RAM (video matrix)  │
 $3800  ├────────────────────────────┤
        │ Westminster charset (2 KB) │
        │ ROM copy + overlaid glyphs │
        └────────────────────────────┘
```

The address format (`$0400`, `0x0400`, `0400h`, `0040:0000`, decimal …), box style, origin direction, and
size-proportional height scaling are all controlled by flags or a JSON `"render"` block — see the skill's `SKILL.md`
for the full schema and parameter reference. A ready-to-run example is bundled under `skills/ascii-memory-map/examples/`.

## Requirements

- Python 3.8+ — standard library only, no `pip install`.

## License

MIT © Rohin Gosling
