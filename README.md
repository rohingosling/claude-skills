# claude-skills

![Claude Code](https://img.shields.io/badge/Claude_Code-marketplace-D97757?style=flat&logo=claude&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=flat&logo=python&logoColor=white)

[Claude Code](https://code.claude.com) **plugin marketplace**. A curated collection of my publicly-shared Agent Skills, each packaged as an installable plugin.

## 📑 Table of Contents

- [📦 Install](#-install)
  - [1. Add the marketplace (once)](#1-add-the-marketplace-once)
  - [2. Install the plugins you want](#2-install-the-plugins-you-want)
  - [3. Activate and use](#3-activate-and-use)
  - [Browse and manage interactively](#browse-and-manage-interactively)
  - [From a terminal, without the prompt](#from-a-terminal-without-the-prompt)
- [🧩 Available plugins](#-available-plugins)
  - [Skill invocation](#skill-invocation)
- [🎨 Showcase](#-showcase)
  - [`g-render-ascii-dependency-graph`](#g-render-ascii-dependency-graph)
  - [`g-render-ascii-hierarchy-diagram`](#g-render-ascii-hierarchy-diagram)
  - [`g-render-ascii-memory-map`](#g-render-ascii-memory-map)
- [📄 License](#-license)

## 📦 Install

These are **Claude Code plugins**, distributed through this repository acting as a **plugin marketplace**. Installing is two ideas: **add the marketplace once**, then **install the plugins you want** from it. If you have never installed a skill before, follow the steps below verbatim — each command is typed at the Claude Code prompt (the `/`-commands) or in a terminal (the `claude …` commands).

The marketplace **id** is `rohingosling-skills`. Every plugin is installed as `<plugin-name>@rohingosling-skills` — the plugin's name (from the table below) plus `@` plus that id.

### 1. Add the marketplace (once)

At the Claude Code prompt:

```text
/plugin marketplace add rohingosling/claude-skills
```

This registers the catalog. You only do this **once per machine**; afterwards every plugin below is available to install.

### 2. Install the plugins you want

**Install one** — name the plugin, `@`, then the marketplace id:

```text
/plugin install g-render-ascii-memory-map@rohingosling-skills
```

**Install several** — run the install line once per plugin:

```text
/plugin install g-render-ascii-dependency-graph@rohingosling-skills
/plugin install g-render-ascii-hierarchy-diagram@rohingosling-skills
```

**Install all of them** — one line per plugin in the [Available plugins](#-available-plugins) table:

```text
/plugin install g-render-ascii-dependency-graph@rohingosling-skills
/plugin install g-render-ascii-hierarchy-diagram@rohingosling-skills
/plugin install g-render-ascii-memory-map@rohingosling-skills
```

### 3. Activate and use

```text
/reload-plugins
```

`/reload-plugins` makes newly installed plugins available in the **current** session (a brand-new session picks them up automatically). Then invoke any skill with its `plugin-name:skill-name` command — see [Skill invocation](#skill-invocation).

### Browse and manage interactively

Prefer a menu to typing commands? Run:

```text
/plugin
```

…then use the **Marketplaces** and **Installed** tabs to browse, install, enable, disable, or remove plugins — no need to remember each plugin's name.

### From a terminal, without the prompt

Everything above is also a normal CLI, handy for a first install or for scripting. The terminal verbs mirror the prompt commands:

```text
claude plugin marketplace add rohingosling/claude-skills
claude plugin install g-render-ascii-memory-map@rohingosling-skills   # repeat per plugin
claude plugin list                                             # confirm what is installed
```

After a terminal install, run `/reload-plugins` (or start a new session) to pick the plugins up.

> **Note:** The `g-` prefix refers to **g**lobal.

## 🧩 Available plugins

| Group | Plugin | What it does |
|-------|--------|--------------|
| ASCII rendering | [`g-render-ascii-dependency-graph`](plugins/g-render-ascii-dependency-graph) | Render an ASCII dependency graph from a JSON structure (horizontal/vertical links, ellipsis markers) for embedding in markdown documentation. |
| ASCII rendering | [`g-render-ascii-hierarchy-diagram`](plugins/g-render-ascii-hierarchy-diagram) | Generate a hierarchical ASCII tree diagram from a JSON structure (folder trees, decomposition diagrams) with aligned comments and two layout modes. |
| ASCII rendering | [`g-render-ascii-memory-map`](plugins/g-render-ascii-memory-map) | Render an ASCII box-drawing memory map (address-space layout diagram) from a JSON structure, for any architecture — Commodore, x86 segmented, ARM/MCU, or flat 32/64-bit — with multiple address formats and size-proportional block heights. |

### Skill invocation

Once a plugin is installed, invoke its skill at the Claude Code prompt as `plugin-name:skill-name`:

```text
/g-render-ascii-dependency-graph:ascii-dependency-graph
/g-render-ascii-hierarchy-diagram:ascii-hierarchy-diagram
/g-render-ascii-memory-map:ascii-memory-map
```

Each skill wraps a dependency-free Python script under its `skills/<skill>/scripts/` directory that can also be run directly (`python3` on macOS/Linux, `python` on Windows).

_More skills will be added over time._

## 🎨 Showcase

Some of the more visual skills are showcased here, starting with the **ASCII rendering** plugins. Each turns a small JSON description into clean, monospace-aligned art ready to paste straight into your docs, or output to your terminal.

### `g-render-ascii-dependency-graph`

Nodes link **horizontally** (`right`) and **vertically** (`bottom`), with an optional `· · ·` ellipsis for truncated branches.

```json
{
    "name": "WebApp",
    "right": { "name": "API Server", "right": { "name": "Router" } },
    "bottom": [
        { "name": "Auth Service", "right": { "name": "JWT" } },
        { "name": "Database", "right": { "name": "Conn Pool" } },
        { "ellipsis": true }
    ]
}
```

```text
┌─────────┐   ┌─────────────┐   ┌─────────┐
│ WebApp  ├──>│ API Server  ├──>│ Router  │
└────┬────┘   └─────────────┘   └─────────┘
     │   ┌───────────────┐   ┌─────┐
     ├──>│ Auth Service  ├──>│ JWT │
     │   └───────────────┘   └─────┘
     │   ┌───────────┐   ┌───────────┐
     ├──>│ Database  ├──>│ Conn Pool │
     │   └───────────┘   └───────────┘
     ·
     ·
     ·
```

### `g-render-ascii-hierarchy-diagram`

A hierarchy with aligned trailing comments — perfect for folder structures and decomposition diagrams.

```json
{
    "name": "my-service",
    "children": [
        { "name": "src", "comment": "Application code", "children": [
            { "name": "main.py", "comment": "Entry point" },
            { "name": "api", "comment": "HTTP route handlers" },
            { "name": "db", "comment": "Persistence layer" } ] },
        { "name": "tests", "comment": "Test suite", "children": [
            { "name": "test_api.py", "comment": "Route tests" } ] },
        { "name": "README.md", "comment": "Project overview" }
    ]
}
```

```text
my-service
├─ src               Application code
│  ├─ main.py        Entry point
│  ├─ api            HTTP route handlers
│  └─ db             Persistence layer
│
├─ tests             Test suite
│  └─ test_api.py    Route tests
│
└─ README.md         Project overview
```

### `g-render-ascii-memory-map`

An address-space layout diagram: boundary addresses in the left **gutter**, region labels **inside** each box, and notes **outside**, arrow-anchored. Block heights are **size-proportional** (here the 12 KB free-RAM region is visibly taller than its 1–2 KB neighbours), and `--show-size` annotates each region with its computed size.

```json
{
    "title": "C64 — VIC bank 0 ($0000-$3FFF)",
    "blocks": [
        { "start": "$0000", "end": "$03FF", "label": "zero page / stack / system",
          "comments": [ "$0001 CHAREN: bit 2 = 0 → char ROM" ] },
        { "start": "$0400", "end": "$07FF", "label": "screen RAM (video matrix)",
          "comments": [ "$D018 bits 4-7 = %0001" ] },
        { "start": "$0800", "end": "$37FF", "label": "free RAM" },
        { "start": "$3800", "end": "$3FFF", "label": "custom charset (2 KB)",
          "comments": [ "$D018 bits 1-3 = %111" ] }
    ]
}
```

```text
C64 — VIC bank 0 ($0000-$3FFF)

 $0000  ┌────────────────────────────┐
        │ zero page / stack / system │ ◄─ $0001 CHAREN: bit 2 = 0 → char ROM
        │ (1 KB)                     │
 $0400  ├────────────────────────────┤
        │ screen RAM (video matrix)  │ ◄─ $D018 bits 4-7 = %0001
        │ (1 KB)                     │
 $0800  ├────────────────────────────┤
        │ free RAM                   │
        │ (12 KB)                    │
        │                            │
        │                            │
        │                            │
        │                            │
 $3800  ├────────────────────────────┤
        │ custom charset (2 KB)      │ ◄─ $D018 bits 1-3 = %111
        │ (2 KB)                     │
        └────────────────────────────┘
```

## 📄 License

Released under the [MIT License](LICENSE) — Copyright © 2026 Rohin Gosling.
