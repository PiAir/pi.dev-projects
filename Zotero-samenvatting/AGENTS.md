# Zotero Abstract Generator — OpenCode Skills

This repo contains a set of OpenCode CLI skills for working with a Zotero library:
generating abstracts for items that have none, searching by title or keyword, and
querying the library directly via SQLite or the command-line interface.

## Skills in this repo

| Skill | Invoke | What it does |
|-------|--------|--------------|
| `zotero-samenvatting` | `/zotero-samenvatting` | Generate abstracts for Zotero items that have none |
| `zotero-zoeken` | `/zotero-zoeken` | Search by title/keyword or by date added; build a CSV for `zotero-samenvatting` |
| `zotero` | *(auto-activated)* | Read-only SQLite access — metadata queries, citation checks, annotation retrieval |
| `zotero-cli` | *(auto-activated)* | Command-line wrapper for `cli-anything-zotero` (`zotero-cli`) |

### Typical end-to-end workflow

```
/zotero-zoeken --recent --days 7 --save sources.csv
    → finds items added this week that have a PDF but no abstract yet

/zotero-samenvatting sources.csv
    → generates and saves an abstract for each pending item
```

---

## What zotero-samenvatting does

For each specified Zotero item:

1. Fetches metadata via the Zotero Local API or CLI
2. Locates the attached PDF
3. Converts the PDF to markdown (text extraction or OCR)
4. The agent reads the markdown and writes a genuine content-based abstract
5. Saves the abstract as `abstractNote` in Zotero
6. Adds the tag `opencode-ai` to the item
7. Sets `status=1` in the CSV file

## Requirements

### Software

- Python 3.10+
- `pymupdf`, `pymupdf4llm`, `pytesseract`, `Pillow`, `requests`
- `zotero-cli` with the CLI Bridge plugin (Zotero must be running for write operations)
- Tesseract OCR (for image-heavy PDFs)

Install Python dependencies:

```bash
pip install -r requirements.txt
```

**Tesseract OCR (optional)** — only needed for scanned/image-heavy PDFs. The script works
without Tesseract but cannot read pages that are stored as images.

- **Windows:** Install via the UB-Mannheim installer: https://github.com/UB-Mannheim/tesseract/wiki  
  After installation, `C:\Program Files\Tesseract-OCR\tesseract.exe` is found automatically.  
  Otherwise set the `TESSERACT_CMD` environment variable to the full path.
- **WSL2/Linux:** `sudo apt install tesseract-ocr tesseract-ocr-nld tesseract-ocr-eng`

### Zotero

- Zotero running locally with the CLI Bridge plugin installed (required for write operations)
- Verify: `zotero-cli app plugin-status` → `"ready": true`
- Local API reachable at `http://localhost:23119`
- The `zotero` and `zotero-zoeken recent` skills read `zotero.sqlite` directly and do **not** require Zotero to be running

### WSL2 (Windows)

Add to `%USERPROFILE%\.wslconfig`:

```ini
[wsl2]
networkingMode=mirrored
```

This allows WSL2 to reach `localhost` on the Windows host.

## Configuration

Set environment variables (or use a `.env` file):

| Variable | Description | Example |
|----------|-------------|---------|
| `ZOTERO_PROFILE_DIR` | Path to Zotero profile directory | `/mnt/c/Users/name/AppData/Roaming/Zotero/Zotero/Profiles/xxx.default` |
| `ZOTERO_DATA_DIR` | Path to Zotero data directory (also used for SQLite access) | `/mnt/c/Users/name/Zotero` |
| `ZOTERO_PDF_BASE` | Base path for PDF files (optional) | `/mnt/c/SynologyDrive/zotero-bijlagen` |
| `ZOTERO_LOCAL_API` | Zotero Local API base URL | `http://localhost:23119` (default) |
| `WORK_DIR` | Working directory for `pdfs/` and `markdown/` | `.` (default: current directory) |
| `PYTHON_CMD` | Full path to Python executable (optional) | `/usr/bin/python3` |
| `TESSERACT_CMD` | Full path to Tesseract binary (optional) | `C:\Program Files\Tesseract-OCR\tesseract.exe` |

Quick setup:

```bash
export ZOTERO_PROFILE_DIR="/mnt/c/Users/your-name/AppData/Roaming/Zotero/Zotero/Profiles/xxx.default"
export ZOTERO_DATA_DIR="/mnt/c/Users/your-name/Zotero"
```

## Invoking the skills

### zotero-samenvatting

```
/zotero-samenvatting ABCD1234
/zotero-samenvatting path/to/sources.csv
```

OpenCode drives the process: it reads the markdown, writes the abstract, and calls the
script to save the result. The script only handles mechanical work.

### zotero-zoeken

```
/zotero-zoeken "machine learning"
/zotero-zoeken "AI" --save results.csv
```

Search by date added (reads `zotero.sqlite` directly — Zotero does not need to be running):

```
/zotero-zoeken --recent --today
/zotero-zoeken --recent --days 7 --save sources.csv
/zotero-zoeken --recent --since 2026-05-01 --save sources.csv
```

By default, `--recent` returns only items with a PDF attachment and no existing abstract —
the exact set that `zotero-samenvatting` needs. Pass `--all-pdf` or `--include-abstract`
to widen the results.

---

## Script subcommands (used internally by OpenCode)

### create_summary.py

```bash
# Fetch metadata + convert PDF; prints JSON with title, authors and markdown preview
python3 scripts/create_summary.py prepare ABCD1234

# Save abstract to Zotero and mark item as done in CSV
python3 scripts/create_summary.py save ABCD1234 sources.csv "The abstract text here."

# List items with status=0 as JSON
python3 scripts/create_summary.py pending sources.csv
```

### zotero_search.py

```bash
# Search by keyword
python3 scripts/zotero_search.py search "<query>" [--scope titleCreatorYear|fields|everything]

# Search by keyword and save to CSV
python3 scripts/zotero_search.py save "<query>" results.csv [--append]

# Search by date added (reads SQLite directly)
python3 scripts/zotero_search.py recent --today
python3 scripts/zotero_search.py recent --days 7
python3 scripts/zotero_search.py recent --since 2026-05-01
python3 scripts/zotero_search.py recent --days 7 --save sources.csv [--append]

# recent flags:
#   --all-pdf           include items without a PDF  (default: PDF-only)
#   --include-abstract  include items that already have an abstract  (default: excluded)
```

## CSV format

The CSV file must have at least three columns:

```csv
zotero_id,title,status
ABCD1234,Title of the article,0
EFGH5678,Another article,1
```

- `zotero_id`: Zotero item key (8 alphanumeric characters)
- `title`: item title (for reference only)
- `status`: `0` = pending, `1` = done

## Working directory layout

The skill expects (and creates) in the working directory:

```
workdir/
├── pdfs/        # downloaded/cached PDF files
├── markdown/    # converted markdown files
└── sources.csv  # CSV file with items to process
```

## Files in this repo

```
AGENTS.md                              # this file
.agents/skills/zotero-samenvatting/
└── SKILL.md                           # skill: generate abstracts for Zotero items
.agents/skills/zotero-zoeken/
└── SKILL.md                           # skill: search by keyword or date; build CSV
.agents/skills/zotero/
└── SKILL.md                           # skill: read-only SQLite access for queries and citation checks
.agents/skills/zotero-cli/
└── SKILL.md                           # skill: zotero-cli command-line wrapper
scripts/
├── create_summary.py                  # per-item pipeline (prepare / save / pending)
├── zotero_search.py                   # search Zotero; recent items by date; write CSV
└── convert_to_md.py                   # PDF → markdown conversion (text + OCR)
```
