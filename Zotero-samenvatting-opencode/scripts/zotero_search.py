#!/usr/bin/env python3
"""
zotero_search.py — Search Zotero by title or keyword; optionally save to CSV.

Subcommands:
  search "<query>" [--scope titleCreatorYear|fields|everything]
      Search Zotero and print results as JSON:
        [{ "id": "...", "title": "..." }, ...]
      Exits with code 1 and a message on stderr if nothing is found.

  save "<query>" <csv_path> [--scope ...] [--append]
      Run the search and write (or append) results to a CSV file with columns
      zotero_id,title,status  (status=0 for all new rows).
      Prints a JSON summary: { "written": N, "csv": "..." }

Configuration via environment variables (see AGENTS.md):
  ZOTERO_PROFILE_DIR
  ZOTERO_DATA_DIR
  ZOTERO_LOCAL_API   default: http://localhost:23119
"""

import csv
import json
import os
import subprocess
import sys
from pathlib import Path

import requests

# ── Configuration ──────────────────────────────────────────────────────────────

PROFILE_DIR = os.environ.get("ZOTERO_PROFILE_DIR", "")
DATA_DIR    = os.environ.get("ZOTERO_DATA_DIR", "")
LOCAL_API   = os.environ.get("ZOTERO_LOCAL_API", "http://localhost:23119")


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
        raise RuntimeError(f"Command failed: {cmd}")
    return r.stdout.strip()


# ── Search ─────────────────────────────────────────────────────────────────────

def _parse_find_output(raw):
    """Parse zotero-cli item find output into list of {id, title} dicts."""
    items = []

    # Try JSON first
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            for obj in parsed:
                key   = obj.get("key") or obj.get("id") or obj.get("itemID")
                title = obj.get("title", "")
                if key:
                    items.append({"id": key, "title": title})
            return items
    except (json.JSONDecodeError, ValueError):
        pass

    # Fall back to line-by-line parsing
    # Common formats: "KEY  Title" or "KEY: Title" or "- KEY — Title"
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        for sep in (" — ", ": ", "\t"):
            if sep in line:
                parts = line.split(sep, 1)
                candidate = parts[0].strip().lstrip("- ").strip()
                if len(candidate) == 8 and candidate.isalnum():
                    items.append({"id": candidate, "title": parts[1].strip()})
                    break

    return items


def search_zotero(query, scope="titleCreatorYear"):
    """Return list of {id, title, has_pdf} dicts matching query."""
    # Try Local API first (more reliable JSON output)
    try:
        resp = requests.get(
            f"{LOCAL_API}/api/users/0/items",
            params={"q": query, "qmode": scope, "format": "json", "limit": 100},
            headers={"Accept": "application/json"},
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            entries = data if isinstance(data, list) else data.get("items", [])

            # Collect parent keys that have a PDF attachment
            pdf_parents = set()
            for obj in entries:
                d = obj.get("data", obj)
                if (d.get("itemType") == "attachment"
                        and d.get("contentType") == "application/pdf"):
                    parent = d.get("parentItem") or d.get("parentKey")
                    if parent:
                        pdf_parents.add(parent)

            items = []
            for obj in entries:
                d         = obj.get("data", obj)
                key       = d.get("key") or obj.get("key")
                title     = d.get("title", "")
                item_type = d.get("itemType", "")
                if key and title and item_type not in ("attachment", "note"):
                    items.append({
                        "id":      key,
                        "title":   title,
                        "has_pdf": key in pdf_parents,
                    })
            if items:
                return items
    except requests.RequestException:
        pass

    # Fallback: CLI (no attachment info available here)
    raw = run(zotero_cli(f'item find "{query}" --scope {scope}'))
    return [dict(item, has_pdf=None) for item in _parse_find_output(raw)]


# ── CSV helpers ────────────────────────────────────────────────────────────────

def _existing_ids(csv_path):
    """Return set of zotero_ids already in the CSV."""
    p = Path(csv_path)
    if not p.exists():
        return set()
    with open(p, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        return {row[0] for row in reader if row}


def write_csv(items, csv_path, append=False):
    """Write items to CSV; return number of rows actually written."""
    p = Path(csv_path)
    existing = _existing_ids(csv_path) if append and p.exists() else set()
    new_items = [i for i in items if i["id"] not in existing]

    if not new_items:
        return 0

    write_header = not (append and p.exists())
    mode = "a" if (append and p.exists()) else "w"

    with open(p, mode, newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["zotero_id", "title", "status"])
        for item in new_items:
            writer.writerow([item["id"], item["title"], 0])

    return len(new_items)


# ── Subcommands ────────────────────────────────────────────────────────────────

def cmd_search(query, scope="titleCreatorYear"):
    items = search_zotero(query, scope)
    if not items:
        print(f"No results for query: {query}", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(items, ensure_ascii=False))


def cmd_save(query, csv_path, scope="titleCreatorYear", append=False):
    items = search_zotero(query, scope)
    if not items:
        print(f"No results for query: {query}", file=sys.stderr)
        sys.exit(1)
    written = write_csv(items, csv_path, append=append)
    print(json.dumps({"written": written, "total_found": len(items), "csv": csv_path}))


# ── Main ───────────────────────────────────────────────────────────────────────

def _get_flag(args, flag, default=None):
    if flag in args:
        idx = args.index(flag)
        if idx + 1 < len(args):
            return args[idx + 1]
    return default


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)

    cmd = args[0]

    try:
        if cmd == "search" and len(args) >= 2:
            query = args[1]
            scope = _get_flag(args, "--scope", "titleCreatorYear")
            cmd_search(query, scope)

        elif cmd == "save" and len(args) >= 3:
            query    = args[1]
            csv_path = args[2]
            scope    = _get_flag(args, "--scope", "titleCreatorYear")
            append   = "--append" in args
            cmd_save(query, csv_path, scope, append)

        else:
            print(__doc__, file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
