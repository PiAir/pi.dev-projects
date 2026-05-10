---
name: zotero-zoeken
description: Search Zotero by title or description and return matching item IDs and titles; optionally save results to a CSV file. Also supports searching by date added (today / last N days / since a specific date).
allowed-tools:
  - Bash
  - Read
  - Write
user-invocable: true
argument-hint: "<query> [--save results.csv] | --recent [--today|--days N|--since YYYY-MM-DD] [--save results.csv]"
---

# Skill: zotero-zoeken

Use this skill to search the Zotero library by title, keyword, or description and retrieve
matching item IDs and titles. Results can optionally be saved to a CSV file.

You can also find items **by date added** — useful for generating a work list for
`zotero-samenvatting` ("add abstracts to everything I added this week").

## When to activate

- The user wants to find a Zotero item by title or topic
- The user wants to look up the Zotero ID for a source they know by name
- The user wants to build a CSV of items matching a topic (e.g. to feed into `zotero-samenvatting`)
- The user asks about items added **today**, **this week**, **last N days**, or **since a specific date**

## Check prerequisites

```bash
zotero-cli app plugin-status   # expected: "ready": true
echo $ZOTERO_PROFILE_DIR       # must not be empty
```

If `ZOTERO_PROFILE_DIR` is missing: ask the user to follow the setup instructions in AGENTS.md.

---

## Workflow A — Search by title / keyword

### Step 1 — Run the search

Use `item find` for title/keyword searches. Always include the full CLI flags.

```bash
python3 scripts/zotero_search.py search "<query>"
```

Or directly with zotero-cli:

```bash
zotero-cli $ZOTERO_CLI_FLAGS item find "<query>" --scope titleCreatorYear
```

Where `$ZOTERO_CLI_FLAGS` expands to:
```
--profile-dir "$ZOTERO_PROFILE_DIR" --data-dir "$ZOTERO_DATA_DIR" --backend api
```

Use `--scope fields` if the title search returns no results (searches all metadata fields).
Use `--scope everything` as a last resort (includes full-text index).

### Step 2 — Present results

Show the user a numbered list. Include a PDF indicator based on the `has_pdf` field:

```
1. ABCD1234 [PDF] — Title of the first result
2. EFGH5678 [no PDF] — Title of the second result
3. IJKL9012 — Title of the third result  (has_pdf: null = unknown, CLI fallback)
...
```

If there are no results: suggest alternative queries or a broader scope.

### Step 3 — Save to CSV (if requested)

If the user wants to save the results (or a selection), write a CSV with columns
`zotero_id,title,status`:

```bash
python3 scripts/zotero_search.py save "<query>" results.csv
```

Or, if the user selects specific items from the list, write only those rows.
`status` is always `0` for newly added items (not yet processed).

---

## Workflow B — Search by date added

Use this workflow when the user asks about items added within a time window, such as:
- "today", "this week", "last 7 days", "since Monday"
- "since 1-5-2026", "since May 1st"
- "items I added recently"

### Step 1 — Translate the time expression to a flag

| User says | Flag to use |
|-----------|-------------|
| "today" | `--today` |
| "this week" / "last week" / "last 7 days" | `--days 7` |
| "last N days" | `--days N` |
| "since YYYY-MM-DD" / "since D-M-YYYY" | `--since YYYY-MM-DD` |

When the user uses a non-ISO date format (e.g. "1-5-2026"), convert it to
`YYYY-MM-DD` (→ `2026-05-01`) before passing it to the script.

### Step 2 — Run the recent search

```bash
python3 scripts/zotero_search.py recent --days 7
python3 scripts/zotero_search.py recent --today
python3 scripts/zotero_search.py recent --since 2026-05-01
```

**Default behaviour (no extra flags needed in most cases):**
- Only items **with a PDF attachment** are returned (`--all-pdf` overrides this)
- Only items **without an existing abstractNote** are returned (`--include-abstract` overrides this)

This means the output is immediately usable as input for `zotero-samenvatting`.

### Step 3 — Present results

The script outputs a JSON list. Show the user a numbered list:

```
Found 5 items added since 2026-05-01 (with PDF, no abstract yet):

1. ABCD1234 — Title of article one  (added: 2026-05-03 14:22:01)
2. EFGH5678 — Title of article two  (added: 2026-05-02 09:15:44)
...
```

If nothing is found:
- Confirm the time window and filters with the user
- Suggest relaxing filters: `--include-abstract` or `--all-pdf`

### Step 4 — Save to CSV and optionally hand off to zotero-samenvatting

Save the results to a CSV file:

```bash
python3 scripts/zotero_search.py recent --days 7 --save sources.csv
```

After saving, ask the user:
> "Found N items. The CSV has been saved to `sources.csv`. Would you like me to
> generate abstracts for these items now using `/zotero-samenvatting sources.csv`?"

If the user confirms, invoke the `zotero-samenvatting` skill with that CSV path.

---

## Multiple results

When a search returns multiple results:
- Show all results with their index, ID and title
- Ask the user which items to use, or whether to save all of them
- Do not silently pick one if there are multiple matches

---

## Error handling

| Problem | Action |
|---------|--------|
| No results (keyword search) | Try `--scope fields`, then `--scope everything`; report if still empty |
| No results (date search) | Confirm time window; suggest `--include-abstract` or `--all-pdf` |
| `ZOTERO_DATA_DIR` not set | Ask the user to set it (needed for SQLite access in `recent`) |
| Zotero unreachable (keyword search) | Check that Zotero is running and `ZOTERO_PROFILE_DIR` is set |
| CSV already exists | Ask whether to append or overwrite; default is append |
