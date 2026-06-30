---
name: ascii-dependency-graph
description: Render an ASCII dependency graph from a JSON structure.
disable-model-invocation: false
---

Render an ASCII dependency graph using the Python script at `${CLAUDE_SKILL_DIR}/scripts/render_ascii_dependency_graph.py`.

## Instructions

1. Construct a JSON object describing the dependency tree. Each node has:
   - `"name"`: the module/dependency name (required)
   - `"right"`: a single node connected horizontally to the right (optional)
   - `"bottom"`: an array of child nodes connected vertically below (optional)
   - Use `{"ellipsis": true}` in a `bottom` array to insert a `· · ·` continuation marker.

2. Write the JSON to a temporary file in the current project's working directory (e.g. `dep_graph.json`).

3. Run (use `python3` on macOS/Linux, `python` on Windows):
   ```
   python3 "${CLAUDE_SKILL_DIR}/scripts/render_ascii_dependency_graph.py" --file dep_graph.json
   ```

4. Copy the output into the target markdown file inside a fenced code block.

5. Delete the temporary JSON file.

## Example JSON

```json
{
    "name": "App",
    "right": {
        "name": "LibA",
        "right": { "name": "LibC" }
    },
    "bottom": [
        { "name": "LibB" },
        {
            "name": "LibD",
            "right": { "name": "LibC" }
        }
    ]
}
```

## Box width rule

Each box has odd character width = RoundUpToNearestOdd( len(name) + 4 ). This ensures the `┬` connector exits exactly from the centre of the bottom border.

## User argument

$ARGUMENTS
