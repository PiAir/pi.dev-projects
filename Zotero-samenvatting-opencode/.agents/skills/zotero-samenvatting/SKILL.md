---
name: zotero-samenvatting
description: Generate abstracts for Zotero items that have none, by converting the attached PDF to markdown and writing a content-based summary.
allowed-tools:
  - Bash
  - Read
  - Write
user-invocable: true
argument-hint: "<ZOTERO_ID or CSV_PATH>"
---

# Skill: zotero-samenvatting

Use this skill to generate abstracts for Zotero items that have none.
The script `scripts/create_summary.py` handles the mechanical work (metadata, PDF,
markdown, saving). You read the markdown and write the abstract.

## When to activate

- The user provides a Zotero item ID (8 alphanumeric characters, e.g. `ABCD1234`)
- The user provides a CSV file with items to process
- The user asks to process pending items

## Check prerequisites

```bash
zotero-cli app plugin-status   # expected: "ready": true
echo $ZOTERO_PROFILE_DIR       # must not be empty
```

If `ZOTERO_PROFILE_DIR` is missing: ask the user to follow the setup instructions in AGENTS.md.

---

## Workflow for a single item

### Step 1 — Prepare

```bash
python3 scripts/create_summary.py prepare <ZOTERO_ID>
```

This prints JSON containing:
- `title` and `authors` — verify these match what the user expects
- `md_preview` — the first 8000 characters of the converted markdown

**Stop if `md_preview` content does not match the title.** Report the mismatch to the user
and do not continue with this item.

### Step 2 — Write the abstract

Read `md_preview` and write an abstract that:
- Contains at most 150 words
- Is based on the actual content, not just the title
- Covers: research question, methodology, key findings, and contribution
- Contains only the abstract text — no preamble, no headers, no quotes
- **Language:** write in Dutch if the source article is in Dutch or Flemish; write in
  English for all other languages

### Step 3 — Save

```bash
python3 scripts/create_summary.py save <ZOTERO_ID> <CSV_PATH> "<abstract>"
```

This saves the abstract as `abstractNote` in Zotero, adds the tag `opencode-ai`, and sets
`status=1` in the CSV file.

---

## Workflow for a CSV

### Get pending items

```bash
python3 scripts/create_summary.py pending <CSV_PATH>
```

Prints a JSON list of items with `status=0`. Process them one by one using the workflow
above (or at most 2–3 in parallel as subagents).

---

## Error handling

| Problem | Action |
|---------|--------|
| PDF not found | Skip item; report to user; continue with next |
| Markdown empty or too short | Check whether the PDF is readable; report |
| Content does not match title | Stop for this item; report mismatch |
| Zotero unreachable | Check that Zotero is running and `ZOTERO_PROFILE_DIR` is set |

## Limits

- At most **2–3 items in parallel** (laptop subagent limit)
- Restart the session if context size approaches 100k tokens
- Always use `pending` to get the current state — do not rely on earlier counts
