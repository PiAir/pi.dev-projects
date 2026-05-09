---
name: zotero-cli
description: >
  Use this skill whenever the user wants to interact with Zotero via the
  cli-anything-zotero CLI tool (zotero-cli) — including searching items,
  managing collections, importing by DOI/PMID, exporting BibTeX, reading
  annotations, running the MCP server, or executing JavaScript in Zotero's
  console. Also use when setting up or troubleshooting zotero-cli on WSL2
  or native Windows (PowerShell), when the user asks about zotero-cli
  commands, or when tasks involve the CLI Bridge plugin.

  Trigger on: "zotero-cli", "cli-anything-zotero", "search my zotero from
  the terminal", "import doi into zotero", "export bibtex via cli",
  "zotero mcp server", "zotero command line".
---

# zotero-cli Skill

Agent-native Zotero CLI (`cli-anything-zotero`) using the Local API backend
(requires Zotero running with CLI Bridge plugin).

## Environment

### Paths

| | WSL2 | Windows (PowerShell) |
|---|---|---|
| Profile dir | `/mnt/c/Users/nswap/AppData/Roaming/Zotero/Zotero/Profiles/75v72gmm.default` | `C:\Users\nswap\AppData\Roaming\Zotero\Zotero\Profiles\75v72gmm.default` |
| Data dir | `/mnt/c/Users/nswap/Zotero` | `C:\Users\nswap\Zotero` |

### Full command line

Always use the full command with `--profile-dir`, `--data-dir`, and `--backend api`. Never rely on aliases — they don't survive between tool calls.

**WSL2 (Bash):**
```bash
zotero-cli --profile-dir "/mnt/c/Users/nswap/AppData/Roaming/Zotero/Zotero/Profiles/75v72gmm.default" --data-dir "/mnt/c/Users/nswap/Zotero" --backend api
```

**Windows (PowerShell):**
```powershell
zotero-cli --profile-dir "C:\Users\nswap\AppData\Roaming\Zotero\Zotero\Profiles\75v72gmm.default" --data-dir "C:\Users\nswap\Zotero" --backend api
```

### Installation

**WSL2:**
```bash
pipx install cli-anything-zotero
```

**Windows (PowerShell):**
```powershell
pip install cli-anything-zotero
# or, if pipx is available:
pipx install cli-anything-zotero
```

### Networking (WSL2 only)

Zotero runs on Windows; WSL2 needs mirrored networking to reach `localhost:23119`.
Configured in `C:\Users\nswap\.wslconfig`:
```ini
[wsl2]
networkingMode=mirrored
```
Without this, all API calls fail with "connection refused". Not needed on native Windows.

### Verify setup

**WSL2:**
```bash
curl http://localhost:23119/api/       # should return "Nothing to see here"
zotero-cli app plugin-status           # should show "ready": true
```

**Windows (PowerShell):**
```powershell
Invoke-RestMethod http://localhost:23119/api/   # should return "Nothing to see here"
zotero-cli app plugin-status                    # should show "ready": true
```

## Prerequisites

- Zotero must be **running** on Windows
- CLI Bridge plugin must be **installed and enabled** (Tools > Add-ons)
- Local API must be enabled: Edit > Settings > Advanced >
  "Allow other applications on this computer to communicate with Zotero" ✓

## Key Commands

The commands themselves are identical on WSL2 and Windows; only the base command prefix (with paths) differs — see the full command lines above.

### Items
```
zotero-cli item list [--limit N]
zotero-cli item find "query" [--collection KEY] [--limit N]
zotero-cli item get KEY
zotero-cli item context KEY               # full metadata for AI use
zotero-cli item annotations KEY           # highlights & notes from PDF
zotero-cli item search-fulltext "query"   # full-text search across PDFs
zotero-cli item bibliography KEY [--style apa]
zotero-cli item analyze KEY [--question "..."]
```

### Collections
```
zotero-cli collection list
zotero-cli collection tree
zotero-cli collection items KEY
zotero-cli collection find "query"
zotero-cli collection stats KEY
```

### Import
```
zotero-cli import doi 10.xxxx/xxxxx [--collection KEY]
zotero-cli import pmid 12345678
zotero-cli import file paper.pdf [--collection KEY]
```

### Export
```
zotero-cli export bib [--collection KEY] [--format bibtex] [--output refs.bib]
```

### MCP Server (for Claude Desktop / Cursor integration)
```
zotero-cli mcp serve
```

### JavaScript execution (advanced)
```
zotero-cli js "return Zotero.Libraries.getAll().map(l => l.name)"
```

## Backend flags

| Flag | When to use |
|------|-------------|
| `--backend api` | Default; Zotero must be running |
| `--backend sqlite` | Offline/read-only; Zotero does NOT need to run |
| `--backend auto` | Tries API first, falls back to SQLite |

Commands marked **"via JS bridge"** require `--backend api` and the CLI Bridge
plugin. SQLite-only commands (list, find, export) work with `--backend sqlite`.

## Installing the CLI Bridge Plugin

If `plugin-status` shows `ready: false`:

**WSL2:**
```bash
zotero-cli app install-plugin
```

**Windows (PowerShell):**
```powershell
zotero-cli app install-plugin
```

Then in Zotero: Tools > Add-ons > gear icon > Install Add-on From File,
select the generated `.xpi` from the profile extensions folder, restart Zotero.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Cannot resolve Zotero profile directory` | Missing `--profile-dir` | Use full command with `--profile-dir` |
| `FileNotFoundError: zotero.sqlite not found` | Missing `--data-dir` | Use full command with `--data-dir` |
| `connection refused` on port 23119 (WSL2) | WSL2 networking not mirrored | Add `networkingMode=mirrored` to `.wslconfig` |
| `connection refused` on port 23119 (Windows) | Zotero not running or Local API disabled | Start Zotero; check Edit > Settings > Advanced |
| `endpoint_active: false` | Zotero not running or plugin not loaded | Start Zotero, check plugin |
| `No such command 'items'` | Wrong command name | Use `item` (singular) |
