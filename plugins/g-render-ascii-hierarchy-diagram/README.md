# g-render-ascii-hierarchy-diagram

![Claude Code](https://img.shields.io/badge/Claude_Code-plugin-D97757?style=flat&logo=claude&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=flat&logo=python&logoColor=white)
![Dependencies](https://img.shields.io/badge/dependencies-none-3DA639?style=flat&logo=python&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-3DA639?style=flat&logo=opensourceinitiative&logoColor=white)

Generate a hierarchical **ASCII tree diagram** from a simple JSON description — folder structures,
decomposition diagrams, or any tree worth rendering as text. Supports **aligned trailing comments** and
two layout modes. Output is ready to paste into a markdown fenced code block.

Packaged as a **Claude Code plugin** (an Agent Skill) wrapping a dependency-free Python script.

## Install

```text
/plugin marketplace add rohingosling/claude-skills
/plugin install g-render-ascii-hierarchy-diagram@rohingosling-skills
/reload-plugins
```

## Usage

Invoke the skill in Claude Code — `/g-render-ascii-hierarchy-diagram:ascii-hierarchy-diagram` — or run the
script directly against a JSON file:

```text
python3 scripts/render_ascii_hierarchy_diagram.py --file hierarchy.json --include-root
python3 scripts/render_ascii_hierarchy_diagram.py --file hierarchy.json --no-include-root
```

(Use `python` instead of `python3` on Windows.)

## JSON shape and modes

Each node has a `"name"` (required), an optional `"comment"` (aligned trailing text), and an optional
`"children"` array.

- **`--include-root`** — render the root and all descendants as one unified tree, with a single global
  comment margin and `│` separators between top-level groups.
- **`--no-include-root`** — skip the root and render each top-level child as an independent tree, each with
  its own comment margin, separated by blank lines.

```json
{
    "name": "project",
    "children": [
        { "name": "src",  "comment": "Source code",   "children": [
            { "name": "main.cpp", "comment": "Entry point" },
            { "name": "utils.h",  "comment": "Helpers" } ] },
        { "name": "docs", "comment": "Documentation", "children": [
            { "name": "README.md", "comment": "Project overview" } ] }
    ]
}
```

```
project
├─ src             Source code
│  ├─ main.cpp     Entry point
│  └─ utils.h      Helpers
│
└─ docs            Documentation
   └─ README.md    Project overview
```

## Requirements

- Python 3.8+ — standard library only, no `pip install`.

## License

MIT © Rohin Gosling
