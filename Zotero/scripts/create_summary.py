#!/usr/bin/env python3
"""
create_summary.py — Mechanische helper voor de zotero-samenvatting skill.

Bedoeld om aangeroepen te worden door pi.dev (of een subagent), niet als
standalone pipeline. pi.dev leest de output en neemt de vervolgstappen.

Subcommando's:
  prepare <ZOTERO_ID>
      Haalt metadata op, lokaliseert de PDF, converteert naar markdown.
      Print JSON naar stdout:
        { "id": "...", "title": "...", "authors": [...], "md_path": "...",
          "md_preview": "<eerste 8000 tekens van de markdown>" }
      Bij fout: exit 1 + foutmelding op stderr.

  save <ZOTERO_ID> <CSV_PAD> <SAMENVATTING>
      Schrijft de samenvatting als abstractNote in Zotero, voegt tag
      'pi.dev-ai' toe, en zet status=1 in het CSV-bestand.

  pending <CSV_PAD>
      Print JSON-lijst van items met status=0:
        [{ "id": "...", "title": "..." }, ...]

Configuratie via omgevingsvariabelen (zie AGENTS.md):
  ZOTERO_PROFILE_DIR   pad naar Zotero-profielmap
  ZOTERO_DATA_DIR      pad naar Zotero-datamap
  ZOTERO_LOCAL_API     standaard: http://localhost:23119
  ZOTERO_PDF_BASE      optioneel basispad voor PDF-bestanden
  WORK_DIR             werkmap voor pdfs/ en markdown/ (standaard: .)
"""

import csv
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import requests

# ── Configuratie ───────────────────────────────────────────────────────────────

PROFILE_DIR = os.environ.get("ZOTERO_PROFILE_DIR", "")
DATA_DIR    = os.environ.get("ZOTERO_DATA_DIR", "")
PDF_BASE    = os.environ.get("ZOTERO_PDF_BASE", "")
LOCAL_API   = os.environ.get("ZOTERO_LOCAL_API", "http://localhost:23119")

WORK_DIR       = Path(os.environ.get("WORK_DIR", ".")).resolve()
PDFS_DIR       = WORK_DIR / "pdfs"
MARKDOWN_DIR   = WORK_DIR / "markdown"
CONVERT_SCRIPT = Path(__file__).parent / "convert_to_md.py"

IS_WINDOWS = sys.platform == "win32"


def python_exe():
    """Return an accessible Python executable for use in subprocesses."""
    import shutil

    # Honour explicit override via environment variable
    override = os.environ.get("PYTHON_CMD")
    if override:
        return override

    # Try candidates in order; use the first one found on PATH
    candidates = ["python", "python3", "py"] if IS_WINDOWS else ["python3", "python"]
    for name in candidates:
        if shutil.which(name):
            return name

    # Last resort: use the same interpreter that is running this script
    return sys.executable


def zotero_cli(args):
    flags = ""
    if PROFILE_DIR:
        flags += f' --profile-dir "{PROFILE_DIR}"'
    if DATA_DIR:
        flags += f' --data-dir "{DATA_DIR}"'
    flags += " --backend api"
    return f"zotero-cli{flags} {args}"


def run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print(r.stderr[:500], file=sys.stderr)
        raise RuntimeError(f"Commando mislukt: {cmd}")
    return r.stdout.strip()


def run_silent(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


# ── Metadata ───────────────────────────────────────────────────────────────────

def fetch_metadata(zotero_id):
    try:
        resp = requests.get(
            f"{LOCAL_API}/api/users/0/items/{zotero_id}",
            headers={"Accept": "application/json"},
            timeout=15,
        )
        if resp.status_code == 200:
            obj = resp.json()
            return obj.get("data", obj)
    except requests.RequestException:
        pass

    out = run(zotero_cli(f"item context {zotero_id}"))
    if out.startswith("["):
        return json.loads(out)[0]
    obj = json.loads(out)
    if isinstance(obj, dict) and "key" in obj:
        return obj

    raise RuntimeError(f"Geen metadata voor {zotero_id}")


# ── PDF zoeken ─────────────────────────────────────────────────────────────────

def _resolve_attachment_path(full_path):
    """
    Resolve a Zotero attachment path to an accessible local path.

    Zotero stores attachment paths differently depending on the platform:
    - Windows native: C:\\SynologyDrive\\zotero-bijlagen\\...
    - WSL2 (via Zotero on Windows): /mnt/c/Users/.../Zotero/C:\\SynologyDrive\\...

    Returns a Path if the file is accessible, otherwise None.
    """
    # WSL2 format: /mnt/c/Users/<name>/Zotero/C:\SynologyDrive\...
    if not IS_WINDOWS and re.match(r"^/mnt/c/Users/[^/]+/Zotero/C:\\", full_path):
        stripped = re.sub(r"^/mnt/c/Users/[^/]+/Zotero/C:\\", "", full_path)
        candidate = Path("/mnt/c/" + stripped.replace("\\", "/"))
        if candidate.exists() and candidate.stat().st_size > 0:
            return candidate

    # Direct path (Windows or Linux)
    candidate = Path(full_path)
    if candidate.exists() and candidate.stat().st_size > 0:
        return candidate

    # PDF_BASE fallback: use just the filename under the configured base dir
    if PDF_BASE:
        candidate = Path(PDF_BASE) / Path(full_path).name
        if candidate.exists() and candidate.stat().st_size > 0:
            return candidate

    return None


def find_pdf(zotero_id):
    PDFS_DIR.mkdir(parents=True, exist_ok=True)
    local_pdf = PDFS_DIR / f"{zotero_id}.pdf"

    if local_pdf.exists() and local_pdf.stat().st_size > 0:
        return str(local_pdf)

    r = run_silent(zotero_cli(f"item context {zotero_id}"))
    if r.returncode == 0:
        for line in r.stdout.split("\n"):
            if line.strip().startswith("- ") and ".pdf:" in line:
                content = line.strip()[2:]
                colon = content.index(": ")
                full_path = content[colon + 2:]

                resolved = _resolve_attachment_path(full_path)
                if resolved:
                    return str(resolved)

    # Fallback: download via Local API
    try:
        resp = requests.get(
            f"{LOCAL_API}/api/items/{zotero_id}/attachments",
            headers={"Accept": "application/json"},
            timeout=15,
        )
        if resp.status_code == 200:
            for att in resp.json():
                if att.get("contentType") == "application/pdf":
                    pdf_data = requests.get(
                        f"{LOCAL_API}/api/items/{att['key']}/content", timeout=30
                    ).content
                    if pdf_data:
                        local_pdf.write_bytes(pdf_data)
                        return str(local_pdf)
    except requests.RequestException:
        pass

    raise RuntimeError(f"Geen PDF gevonden voor {zotero_id}")


# ── PDF → markdown ─────────────────────────────────────────────────────────────

def convert_pdf(pdf_path, zotero_id):
    MARKDOWN_DIR.mkdir(parents=True, exist_ok=True)
    run(f'{python_exe()} "{CONVERT_SCRIPT}" "{pdf_path}" "{MARKDOWN_DIR}"')

    md_path = MARKDOWN_DIR / f"{zotero_id}.md"
    if md_path.exists() and md_path.stat().st_size > 100:
        return str(md_path)

    candidates = sorted(
        (p for p in MARKDOWN_DIR.glob("*.md") if p.stat().st_size > 100),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise RuntimeError("Conversie leverde geen bruikbaar markdown-bestand op")

    renamed = MARKDOWN_DIR / f"{zotero_id}.md"
    if not renamed.exists():
        candidates[0].rename(renamed)
    return str(renamed)


# ── Zotero + CSV schrijven ─────────────────────────────────────────────────────

def save_to_zotero(zotero_id, summary):
    run(zotero_cli(f'item update {zotero_id} --field "abstractNote={summary}"'))
    r = run_silent(zotero_cli(f"item tag {zotero_id}"))
    if "pi.dev-ai" not in r.stdout:
        run(zotero_cli(f"item tag {zotero_id} --add pi.dev-ai"))


def save_to_csv(csv_path, zotero_id, status=1):
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            if row and row[0] == zotero_id:
                row[2] = str(status)
            rows.append(row)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


# ── Subcommando's ──────────────────────────────────────────────────────────────

def cmd_prepare(zotero_id):
    meta = fetch_metadata(zotero_id)
    title = meta.get("title", "Onbekend")
    authors = [
        c.get("name") or c.get("lastName", "")
        for c in meta.get("creators", [])
        if c.get("creatorType") and (c.get("name") or c.get("lastName"))
    ]
    pdf_path = find_pdf(zotero_id)
    md_path  = convert_pdf(pdf_path, zotero_id)
    preview  = Path(md_path).read_text(encoding="utf-8")[:8000]

    print(json.dumps({
        "id":         zotero_id,
        "title":      title,
        "authors":    authors,
        "md_path":    md_path,
        "md_preview": preview,
    }, ensure_ascii=False))


def cmd_save(zotero_id, csv_path, summary):
    save_to_zotero(zotero_id, summary)
    save_to_csv(csv_path, zotero_id, status=1)
    print(json.dumps({"status": "ok", "id": zotero_id}))


def cmd_pending(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # sla header over
        items = [
            {"id": row[0], "title": row[1]}
            for row in reader
            if row and row[2].strip() == "0"
        ]
    print(json.dumps(items, ensure_ascii=False))


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)

    cmd = args[0]

    try:
        if cmd == "prepare" and len(args) == 2:
            cmd_prepare(args[1])
        elif cmd == "save" and len(args) == 4:
            cmd_save(args[1], args[2], args[3])
        elif cmd == "pending" and len(args) == 2:
            cmd_pending(args[1])
        else:
            print(__doc__, file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Fout: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
