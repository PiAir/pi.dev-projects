# Zotero OpenCode Skills

Two [OpenCode](https://opencode.ai) CLI skills for working with your Zotero library:

| Skill | Command | What it does |
|-------|---------|--------------|
| `zotero-samenvatting` | `/zotero-samenvatting` | Generates an abstract for a Zotero item by reading its PDF |
| `zotero-zoeken` | `/zotero-zoeken` | Searches your Zotero library by title or keyword |

---

## Requirements

### Zotero

- [Zotero 7 or 8](https://www.zotero.org) running locally
- [cli-anything-zotero](https://github.com/PiaoyangGuohai1/cli-anything-zotero) plugin installed and active
- Verify: `zotero-cli app plugin-status` → `"ready": true`

### Python

Python 3.10+ with the following packages:

```bash
pip install -r requirements.txt
```

| Package | Used for |
|---------|----------|
| `pymupdf` | PDF parsing |
| `pymupdf4llm` | PDF → markdown conversion |
| `Pillow` | Image handling for OCR |
| `requests` | Zotero Local API calls |
| `pytesseract` | OCR for scanned PDFs *(optional)* |

### Tesseract OCR *(optional)*

Only needed if your PDFs are scanned (image-based rather than text-based).
The scripts work without it but will produce empty output for image-only pages.

- **Windows:** Install via the [UB-Mannheim installer](https://github.com/UB-Mannheim/tesseract/wiki).
  The default install path (`C:\Program Files\Tesseract-OCR\tesseract.exe`) is found automatically.
- **WSL2 / Linux:** `sudo apt install tesseract-ocr tesseract-ocr-nld tesseract-ocr-eng`

### WSL2 networking *(Windows only)*

If running the scripts from WSL2, Zotero runs on the Windows host. Add this to
`%USERPROFILE%\.wslconfig` so WSL2 can reach `localhost:23119`:

```ini
[wsl2]
networkingMode=mirrored
```

---

## Configuration

Copy `.env.sample` to `.env` and fill in your paths:

```bash
# Linux / WSL2
cp .env.sample .env && source .env

# Windows (PowerShell)
Copy-Item .env.sample .env
# Edit .env, then load into the current session:
Get-Content .env | Where-Object { $_ -notmatch '^#' -and $_ -match '=' } | ForEach-Object { $k,$v = $_ -split '=',2; [System.Environment]::SetEnvironmentVariable($k.Trim(), $v.Trim()) }
```

The required and optional variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ZOTERO_PROFILE_DIR` | Yes | — | Path to your Zotero profile directory |
| `ZOTERO_DATA_DIR` | Yes | — | Path to your Zotero data directory |
| `ZOTERO_LOCAL_API` | No | `http://localhost:23119` | Zotero Local API base URL |
| `ZOTERO_PDF_BASE` | No | — | Base path for PDFs stored outside the Zotero data dir |
| `WORK_DIR` | No | current directory | Where `pdfs/` and `markdown/` cache folders are created |
| `TESSERACT_CMD` | No | auto-detected | Full path to the Tesseract executable |

**Finding your Zotero paths:** In Zotero, go to *Edit → Settings → Advanced* and look
at the "Data Directory Location". The profile directory is shown under *Help → About Zotero*
(click the path to open it).

---

## Skills

### `/zotero-samenvatting` — Generate abstracts

Generates a content-based abstract (max. 150 words) for one or more Zotero items that
have no abstract yet.

**Usage:**

```
/zotero-samenvatting ABCD1234
/zotero-samenvatting path/to/sources.csv
```

**What happens:**

1. Fetches item metadata from Zotero
2. Locates the attached PDF (local cache → SynologyDrive/linked path → Local API download)
3. Converts the PDF to markdown (text extraction, with OCR fallback for scanned pages)
4. The agent reads the markdown and writes a genuine abstract based on the content
5. Saves the abstract as `abstractNote` in Zotero and adds the tag `opencode-ai`
6. Sets `status=1` in the CSV file

**Language rule:** Dutch source → Dutch abstract. Any other language → English abstract.

**CSV format** (for batch processing):

```csv
zotero_id,title,status
ABCD1234,Title of the article,0
EFGH5678,Another article,1
```

`status=0` means pending; `status=1` means done.

---

### `/zotero-zoeken` — Search Zotero

Searches your Zotero library by title or keyword and returns matching item IDs and titles.
Results can be saved to a CSV file for further processing (e.g. with `zotero-samenvatting`).

**Usage:**

```
/zotero-zoeken artificial intelligence in education
/zotero-zoeken "large language models" --save results.csv
```

**What happens:**

1. Searches Zotero using `item find` (title/creator/year scope by default)
2. Falls back to `--scope fields` or `--scope everything` if no results are found
3. Presents a numbered list of matches with ID and title
4. Saves to CSV on request — with `--append` to add to an existing file without duplicates

---

## Scripts

The skills call these scripts internally. You can also run them directly.

### `scripts/create_summary.py`

Mechanical pipeline helper for `zotero-samenvatting`. Three subcommands:

```bash
# Fetch metadata + convert PDF to markdown; prints JSON with title, authors, markdown preview
python3 scripts/create_summary.py prepare ABCD1234

# Save an abstract to Zotero and mark the item as done in the CSV
python3 scripts/create_summary.py save ABCD1234 sources.csv "The abstract text."

# List items with status=0 as JSON
python3 scripts/create_summary.py pending sources.csv
```

### `scripts/zotero_search.py`

Search helper for `zotero-zoeken`. Two subcommands:

```bash
# Search and print results as JSON
python3 scripts/zotero_search.py search "machine learning"
python3 scripts/zotero_search.py search "neural network" --scope fields

# Search and write results to CSV (--append to add without overwriting)
python3 scripts/zotero_search.py save "deep learning" results.csv
python3 scripts/zotero_search.py save "AI education" results.csv --append
```

### `scripts/convert_to_md.py`

Converts a PDF to markdown. Used internally by `create_summary.py`.

```bash
python3 scripts/convert_to_md.py path/to/file.pdf [output-dir]
```

Uses text extraction where possible; falls back to Tesseract OCR for image-heavy pages.

---

## Repository layout

```
README.md
AGENTS.md                                   # full setup instructions (for OpenCode)
.env.sample                                 # environment variable template
requirements.txt                            # Python dependencies
.gitignore
.agents/skills/
├── zotero-samenvatting/
│   └── SKILL.md                            # skill instructions for OpenCode
└── zotero-zoeken/
    └── SKILL.md                            # skill instructions for OpenCode
scripts/
├── create_summary.py                       # pipeline: prepare / save / pending
├── zotero_search.py                        # search: search / save
└── convert_to_md.py                        # PDF → markdown
```
