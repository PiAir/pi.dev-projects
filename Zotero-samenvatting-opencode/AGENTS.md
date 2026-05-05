# Zotero Abstract Generator — OpenCode Skill

This repo contains an OpenCode CLI skill that automatically generates abstracts for
Zotero items that have none.

## What the skill does

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
- `zotero-cli` with the CLI Bridge plugin (Zotero must be running)
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

- Zotero running locally with the CLI Bridge plugin installed
- Verify: `zotero-cli app plugin-status` → `"ready": true`
- Local API reachable at `http://localhost:23119`

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
| `ZOTERO_DATA_DIR` | Path to Zotero data directory | `/mnt/c/Users/name/Zotero` |
| `ZOTERO_PDF_BASE` | Base path for PDF files (optional) | `/mnt/c/SynologyDrive/zotero-bijlagen` |
| `ZOTERO_LOCAL_API` | Zotero Local API base URL | `http://localhost:23119` (default) |
| `WORK_DIR` | Working directory for `pdfs/` and `markdown/` | `.` (default: current directory) |

Quick setup:

```bash
export ZOTERO_PROFILE_DIR="/mnt/c/Users/your-name/AppData/Roaming/Zotero/Zotero/Profiles/xxx.default"
export ZOTERO_DATA_DIR="/mnt/c/Users/your-name/Zotero"
```

## Invoking the skill

The skill lives in `.agents/skills/zotero-samenvatting/`. Invoke via OpenCode CLI:

```
/zotero-samenvatting ABCD1234
/zotero-samenvatting path/to/sources.csv
```

OpenCode drives the process: it reads the markdown, writes the abstract, and calls the
script to save the result. The script only handles mechanical work.

### Script subcommands (used internally by OpenCode)

```bash
# Fetch metadata + convert PDF; prints JSON with title, authors and markdown preview
python3 scripts/create_summary.py prepare ABCD1234

# Save abstract to Zotero and mark item as done in CSV
python3 scripts/create_summary.py save ABCD1234 sources.csv "The abstract text here."

# List items with status=0 as JSON
python3 scripts/create_summary.py pending sources.csv
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
└── SKILL.md                           # skill: search Zotero by title or keyword
scripts/
├── create_summary.py                  # per-item pipeline (prepare / save / pending)
├── zotero_search.py                   # search Zotero; optionally write results to CSV
└── convert_to_md.py                   # PDF → markdown conversion (text + OCR)
```
