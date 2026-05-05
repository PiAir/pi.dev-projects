---
name: zotero-zoeken
description: Search Zotero by title or description and return matching item IDs and titles; optionally save results to a CSV file.
allowed-tools:
  - Bash
  - Read
  - Write
user-invocable: true
argument-hint: "<query> [--save results.csv]"
---

# Skill: zotero-zoeken

Use this skill to search the Zotero library by title, keyword, or description and retrieve
matching item IDs and titles. Results can optionally be saved to a CSV file.

## When to activate

- The user wants to find a Zotero item by title or topic
- The user wants to look up the Zotero ID for a source they know by name
- The user wants to build a CSV of items matching a topic (e.g. to feed into `zotero-samenvatting`)

## Check prerequisites

```bash
zotero-cli app plugin-status   # expected: "ready": true
echo $ZOTERO_PROFILE_DIR       # must not be empty
```

If `ZOTERO_PROFILE_DIR` is missing: ask the user to follow the setup instructions in AGENTS.md.

---

## Workflow

### Step 1 — Run the search

Use `item find` for title/keyword searches. Always include the full CLI flags.

```bash
python3 scripts/zotero_search.py "<query>"
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
python3 scripts/zotero_search.py "<query>" --save results.csv
```

Or, if the user selects specific items from the list, write only those rows.
`status` is always `0` for newly added items (not yet processed).

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
| No results | Try `--scope fields`, then `--scope everything`; report if still empty |
| Zotero unreachable | Check that Zotero is running and `ZOTERO_PROFILE_DIR` is set |
| CSV already exists | Ask whether to append or overwrite; default is append |
