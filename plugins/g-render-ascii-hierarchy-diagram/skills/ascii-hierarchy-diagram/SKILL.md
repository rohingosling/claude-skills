---
name: ascii-hierarchy-diagram
description: Generate a hierarchical ASCII diagram that can be used for representing folder structures, decomposition diagrams, or any other kind of diagrams that might benefit from being represented by an ASCII hierarchy diagram.
disable-model-invocation: false
---

Render a hierarchical ASCII tree diagram using the Python script at `${CLAUDE_SKILL_DIR}/scripts/render_ascii_hierarchy_diagram.py`.

## Instructions

1. Construct a JSON object describing the hierarchy tree. Each node has:
   - `"name"`: the node label (required)
   - `"comment"`: a trailing comment displayed after the node (optional)
   - `"children"`: an array of child nodes (optional)

2. Write the JSON to a temporary file in the current project's working directory (e.g. `hierarchy.json`).

3. Run with one of two modes (use `python3` on macOS/Linux, `python` on Windows):

   Include the root node in the output:
   ```
   python3 "${CLAUDE_SKILL_DIR}/scripts/render_ascii_hierarchy_diagram.py" --file hierarchy.json --include-root
   ```

   Skip the root node and render each top-level child as an independent tree:
   ```
   python3 "${CLAUDE_SKILL_DIR}/scripts/render_ascii_hierarchy_diagram.py" --file hierarchy.json --no-include-root
   ```

4. Copy the output into the target markdown file inside a fenced code block.

5. Delete the temporary JSON file.

## Modes

- **`--include-root`**: Render the root node and all descendants as a single unified tree. One global comment margin is computed across the entire tree. A blank separator line (carrying the `│` continuation glyph at the relevant column) is inserted after every completed sub-tree at every depth — that is, after any node that has its own children and is not the last sibling. Leaf entries and final siblings get no gap.

- **`--no-include-root`**: Skip the root node. Render each top-level child as a separate independent tree. Each group computes its own comment margin. Groups are separated by a blank line, and within each group sub-trees are gapped at every depth by the same rule as `--include-root`.

## Comment alignment

Comments are aligned to a margin computed as: length of the longest `prefix + name` string + 4. This margin is global in `--include-root` mode and per-group in `--no-include-root` mode.

## Example JSON

```json
{
    "name": "project",
    "children": [
        {
            "name": "src",
            "comment": "Source code",
            "children": [
                { "name": "main.cpp", "comment": "Entry point" },
                { "name": "utils.h", "comment": "Helpers" }
            ]
        },
        {
            "name": "docs",
            "comment": "Documentation",
            "children": [
                { "name": "README.md", "comment": "Project overview" }
            ]
        }
    ]
}
```

### Output with `--include-root`

```
project
├─ src             Source code
│  ├─ main.cpp     Entry point
│  └─ utils.h      Helpers
│
└─ docs            Documentation
   └─ README.md    Project overview
```

### Output with `--no-include-root`

```
src            Source code
├─ main.cpp    Entry point
└─ utils.h     Helpers

docs            Documentation
└─ README.md    Project overview
```

## User argument

$ARGUMENTS
