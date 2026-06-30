# g-render-ascii-dependency-graph

![Claude Code](https://img.shields.io/badge/Claude_Code-plugin-D97757?style=flat&logo=claude&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=flat&logo=python&logoColor=white)
![Dependencies](https://img.shields.io/badge/dependencies-none-3DA639?style=flat&logo=python&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-3DA639?style=flat&logo=opensourceinitiative&logoColor=white)

Render a clean **ASCII dependency graph** from a simple JSON description, ready to paste into a markdown
fenced code block. Nodes connect **horizontally** (`right`) and **vertically** (`bottom`), with an optional
`· · ·` ellipsis marker for truncated branches. Box widths are computed so the connectors line up exactly.

Packaged as a **Claude Code plugin** (an Agent Skill) wrapping a dependency-free Python script.

## Install

```text
/plugin marketplace add rohingosling/claude-skills
/plugin install g-render-ascii-dependency-graph@rohingosling-skills
/reload-plugins
```

## Usage

Invoke the skill in Claude Code — `/g-render-ascii-dependency-graph:ascii-dependency-graph` — or run the
script directly against a JSON file:

```text
python3 scripts/render_ascii_dependency_graph.py --file dep_graph.json
```

(Use `python` instead of `python3` on Windows.)

## JSON shape

Each node has a `"name"` (required), an optional single `"right"` node (horizontal link), and an optional
`"bottom"` array of child nodes (vertical links). Insert `{"ellipsis": true}` in a `bottom` array for a
`· · ·` continuation marker.

```json
{
    "name": "App",
    "right": { "name": "LibA", "right": { "name": "LibC" } },
    "bottom": [
        { "name": "LibB" },
        { "name": "LibD", "right": { "name": "LibC" } }
    ]
}
```

## Requirements

- Python 3.8+ — standard library only, no `pip install`.

## License

MIT © Rohin Gosling
