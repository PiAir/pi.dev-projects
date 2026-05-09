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

  recent [--today|--days N|--since YYYY-MM-DD] [--all-pdf] [--include-abstract]
         [--save <csv_path>] [--append]
      Find items added to Zotero within a time window. Reads zotero.sqlite
      directly (read-only). By default returns only items that have a PDF
      attachment AND have no abstractNote (ready for zotero-samenvatting).
      Flags:
        --today            Items added since midnight today (local time)
        --days N           Items added in the last N days  (default: 7)
        --since YYYY-MM-DD Items added on or after this date
        --all-pdf          Include items without a PDF attachment
        --include-abstract Include items that already have an abstractNote
        --save <path>      Write results to CSV instead of printing JSON
        --append           Append to existing CSV (skip duplicate IDs)
      Prints a JSON list: [{ "id": "...", "title": "...", "has_pdf": true,
                             "date_added": "YYYY-MM-DD HH:MM:SS" }, ...]

Configuration via environment variables (see AGENTS.md):
  ZOTERO_PROFILE_DIR
  ZOTERO_DATA_DIR
  ZOTERO_LOCAL_API   default: http://localhost:23119
"""

import csv
import datetime
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
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


# ── SQLite helpers ─────────────────────────────────────────────────────────────

def _get_copyable_db_path():
    """Return the path to zotero.sqlite, derived from ZOTERO_DATA_DIR."""
    if DATA_DIR:
        return str(Path(DATA_DIR) / "zotero.sqlite")
    # Fallback: try to detect WSL2 or Windows default paths
    import platform
    if sys.platform == "linux" and Path("/mnt/c/Users").exists():
        import glob as _glob
        candidates = _glob.glob("/mnt/c/Users/*/Zotero/zotero.sqlite")
        if candidates:
            return candidates[0]
    raise RuntimeError(
        "Cannot locate zotero.sqlite. Set ZOTERO_DATA_DIR in your environment."
    )


def _open_sqlite():
    """
    Open zotero.sqlite in read-only mode.  If the live database is locked
    (because Zotero is writing), open a temporary copy instead.
    """
    src = _get_copyable_db_path()

    # Try live database first (fastest, no extra I/O)
    try:
        uri = Path(src).as_uri() + "?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
        conn.execute("SELECT 1")
        return conn
    except sqlite3.OperationalError:
        pass  # locked — fall through to temp copy

    # Make a snapshot copy in a temp directory and open that
    tmp_dir = tempfile.mkdtemp(prefix="zotero_db_")
    dst = os.path.join(tmp_dir, "zotero.sqlite")
    shutil.copy2(src, dst)
    uri = Path(dst).as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)

    # Register cleanup so the temp file doesn't linger
    import atexit
    atexit.register(shutil.rmtree, tmp_dir, ignore_errors=True)

    return conn


def _since_clause(today=False, days=None, since=None):
    """
    Return (where_fragment, params) for the dateAdded filter.
    dateAdded in Zotero is stored as an ISO-8601 string: 'YYYY-MM-DD HH:MM:SS'
    """
    if since:
        # Accept both 'YYYY-MM-DD' and 'YYYY-MM-DDTHH:MM:SS'
        cutoff = since.replace("T", " ")
        if len(cutoff) == 10:
            cutoff += " 00:00:00"
        return "i.dateAdded >= ?", [cutoff]
    if today:
        cutoff = datetime.date.today().strftime("%Y-%m-%d") + " 00:00:00"
        return "i.dateAdded >= ?", [cutoff]
    # Default: last N days (default 7)
    n = int(days) if days is not None else 7
    cutoff = (datetime.datetime.utcnow() - datetime.timedelta(days=n)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    return "i.dateAdded >= ?", [cutoff]


def search_recent(today=False, days=None, since=None,
                  pdf_only=True, no_abstract=True):
    """
    Return items added within the given time window.

    Each result: { "id": key, "title": ..., "has_pdf": bool, "date_added": str }

    pdf_only    — when True (default) only items with a PDF attachment are returned
    no_abstract — when True (default) only items without an abstractNote are returned
    """
    date_clause, params = _since_clause(today=today, days=days, since=since)

    conn = _open_sqlite()
    try:
        cur = conn.cursor()

        # Items with their key, title, dateAdded, and whether they have a PDF
        sql = f"""
            SELECT DISTINCT
                i.key                    AS zotero_id,
                tv.value                 AS title,
                i.dateAdded              AS date_added,
                CASE WHEN att.itemID IS NOT NULL THEN 1 ELSE 0 END AS has_pdf,
                av.value                 AS abstract
            FROM items i
            JOIN itemTypes it2 ON i.itemTypeID = it2.itemTypeID
            JOIN itemData td   ON i.itemID = td.itemID AND td.fieldID = 1
            JOIN itemDataValues tv ON td.valueID = tv.valueID
            LEFT JOIN (
                SELECT parentItemID, itemID
                FROM itemAttachments
                WHERE contentType = 'application/pdf'
            ) att ON att.parentItemID = i.itemID
            LEFT JOIN itemData ad ON i.itemID = ad.itemID AND ad.fieldID = 2
            LEFT JOIN itemDataValues av ON ad.valueID = av.valueID
            WHERE it2.typeName NOT IN ('attachment', 'note')
              AND i.itemID NOT IN (SELECT itemID FROM deletedItems)
              AND {date_clause}
            ORDER BY i.dateAdded DESC
        """
        cur.execute(sql, params)
        rows = cur.fetchall()
    finally:
        conn.close()

    results = []
    for zotero_id, title, date_added, has_pdf_int, abstract in rows:
        has_pdf = bool(has_pdf_int)
        if pdf_only and not has_pdf:
            continue
        if no_abstract and abstract:
            continue
        results.append({
            "id":         zotero_id,
            "title":      title or "",
            "has_pdf":    has_pdf,
            "date_added": date_added or "",
        })
    return results


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

def cmd_recent(today=False, days=None, since=None,
               pdf_only=True, no_abstract=True,
               csv_path=None, append=False):
    items = search_recent(today=today, days=days, since=since,
                          pdf_only=pdf_only, no_abstract=no_abstract)
    if not items:
        print("No matching items found for the given time window.", file=sys.stderr)
        sys.exit(1)

    if csv_path:
        written = write_csv(items, csv_path, append=append)
        print(json.dumps({
            "written": written,
            "total_found": len(items),
            "csv": csv_path,
        }))
    else:
        print(json.dumps(items, ensure_ascii=False))


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

        elif cmd == "recent":
            today       = "--today" in args
            days        = _get_flag(args, "--days")
            since       = _get_flag(args, "--since")
            pdf_only    = "--all-pdf" not in args          # default: pdf only
            no_abstract = "--include-abstract" not in args  # default: no abstract
            csv_path    = _get_flag(args, "--save")
            append      = "--append" in args
            cmd_recent(today=today, days=days, since=since,
                       pdf_only=pdf_only, no_abstract=no_abstract,
                       csv_path=csv_path, append=append)

        else:
            print(__doc__, file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
