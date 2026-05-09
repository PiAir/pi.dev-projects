# AGENTS.md

This file provides guidance for pi when working with this YouTube Interactive Lesson Builder.

## Pi Configuration

This project is a **pi package** (`package.json` with `pi` key). Skills are discovered from `.pi/skills/`, extensions from `.pi/extensions/`, and prompts from `.pi/prompts/`.

To install locally:
```bash
pi install -l .
```

## Agent Instructions
- Avoid repetition: If a tool call fails or gives the same result, try a different strategy.
- Be action-oriented: Use the <think> tags only for necessary planning. Then proceed directly to tool usage.

## Guardrails (check first — read before doing anything)

### 🔴 DO NOT (failure checklist)
If you break any of these, the result will be broken. No exceptions.

1. **Never write `index.html` from scratch** — always copy `extensions/lesson-template.html` as your starting point
2. **Never use camelCase in Vue `setup()` return** — browser lowercases all identifiers
3. **Never skip Dutch (`nl`) subtitles** — every lesson MUST have Dutch subtitles
4. **Never use `max-height` + `aspect-ratio`** on the same element
5. **Never use `>` inside `{{ }}` expressions** — use `v-if`/`v-else`
6. **Never start the HTTP server yourself** — instruct the user to do it

### ✅ MUST HAVE before handing to user
- [ ] `index.html` is a copy of `extensions/lesson-template.html` (not written from scratch)
- [ ] All reactive state in `setup()` return uses lowercase names only
- [ ] `subtitles_en.vtt` **and** `subtitles_nl.vtt` both exist in the project folder
- [ ] `lesson-data.json` `subtitleLangs` includes `"nl"` (e.g. `["en", "nl"]`)
- [ ] No Vue warnings in the browser console
- [ ] `lesson-data.json` is valid JSON
- [ ] (if `--pdf`) `samenvatting_*.pdf` exists and is non-empty

These guardrails exist because past runs broke in exactly these ways:
- Writing HTML from scratch → Vue camelCase failures → silent broken UI
- Skipping Dutch subtitle download → incomplete lesson with only English subs
- Starting the HTTP server → user confusion about which URL to open

### Hard-won Lessons

These mistakes have already been made and fixed. Do not repeat them.

### Vue 3 in-DOM templates: use only lowercase reactive state

When Vue 3 is used via CDN in a plain HTML file, the browser parses the HTML before Vue compiles it and **lowercases all identifiers**. Any camelCase name returned from `setup()` becomes inaccessible after the first reactive update.

**Rule: all reactive state returned from `setup()` must use only lowercase names.**

```javascript
// WRONG — breaks after first reactive update:
const activeChapter = ref(0);
const quizQuestions = ref([]);
const selectedAnswer = ref(null);
const subLang = ref('nl');

// CORRECT:
const chapter = ref(0);
const questions = ref([]);
const answer = ref(null);
const sublang = ref('nl');
```

Also rename `v-for` loop variables that collide with state: use `v-for="t in tabs"` not `v-for="tab in tabs"`.

### `>` inside `{{ }}` expressions corrupts the template

The browser HTML parser sees `>` in a mustache expression as closing a tag. Use HTML entities or `v-if`/`v-else`:

```html
<!-- WRONG: -->
{{ qidx < questions.length-1 ? 'Volgende →' : 'Resultaten' }}

<!-- CORRECT: -->
<span v-if="qidx < questions.length-1">Volgende &rarr;</span>
<span v-else>Resultaten</span>
```

### Video sizing: `height` + `aspect-ratio`, NOT `max-height` + `aspect-ratio`

`max-height` + `aspect-ratio` on the same element conflict — the browser clips the height without adjusting the width.

```css
/* CORRECT: */
#player-wrapper { position: relative; height: 42vh; aspect-ratio: 16 / 9; max-width: 100%; }
#player-wrapper iframe, #player-wrapper > div { position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0; }
```

Pass `width: '100%', height: '100%'` to `new YT.Player(...)` — the API defaults to 640×390.

### Subtitle bar: below the iframe, not overlaid

CSS overlays on YouTube iframes are unreliable. Place the subtitle bar as a **sibling** below `#player-wrapper`.

### CRLF line endings break VTT parsing

VTT files may have CRLF (`\r\n`) or LF (`\n`) line endings. Always normalize before parsing:

```python
content = content.replace('\r\n', '\n').replace('\r', '\n')
```

Without this, `re.split(r'\n\n+', content)` treats the entire file as one block — all subtitles appear simultaneously.

### UTF-8 double-encoding (mojibake) destroys non-ASCII characters

When JSON data files contain non-ASCII characters (Dutch accented letters like é, ë, ö), Python's `json.dump` **default `ensure_ascii=True` will escape them as `\u00e9` etc.** If these are then written with a different encoding or read back incorrectly, the result is **mojibake**: `Ã©` instead of `é`, `â€"` instead of `—`, `Ã«` instead of `ë`. This is a common silent corruption that makes subtitle text unreadable in any editor.

**Always use `ensure_ascii=False` and explicit `encoding='utf-8'` when writing JSON data files:**

```python
import json

# WRONG — escapes non-ASCII, risking mojibake:
json.dump(data, f, ensure_ascii=True)   # default!

# CORRECT — write actual UTF-8 characters:
json.dump(data, f, ensure_ascii=False, indent=2)
```

**Always write binary (`'wb'`) and read binary (`'rb'`) for VTT files to avoid system encoding issues on Windows.** On Windows, `open('file', 'r')` uses `cp1252` by default, not UTF-8 — non-ASCII characters get corrupted.

```python
# CORRECT — always explicit encoding:
with open('subtitles_nl.vtt', 'w', encoding='utf-8') as f:
    f.write(content)
```

**Always use `TextDecoder('utf-8')` + `arrayBuffer()` in the browser instead of `res.text()`** to avoid any codepage ambiguity:

```javascript
const buf = await res.arrayBuffer();
const text = new TextDecoder('utf-8').decode(buf);
```

**Verify before handing to user:** Open JSON/VTT files in any editor that supports UTF-8. If you see `Ã©` or `â€"` or `Ã«` anywhere, the file is corrupted and must be fixed before the user sees it.

### YouTube rolling-caption VTT format

Each cue block contains the *previous* sentence plus one new word with inline `<c>word</c>` tags. To get clean display cues:
1. Strip all `<tag>` content
2. Take only the **last text line** of each block
3. Skip cues shorter than 0.05 s
4. Deduplicate consecutive identical lines by extending the previous cue's end time

### Strip `>>` speaker markers

YouTube uses `>>` to mark speaker changes. Strip these from display text:

```python
clean = re.sub(r'^>>\s*', '', text).strip()
clean = re.sub(r'\s*>>\s*', ' ', clean).strip()
```

### Quiz answer option length must be uniform

Students recognize the correct answer because it's usually the longest. Write all four options at similar length — extend wrong answers with plausible-but-incorrect detail rather than short decoys.

### Split data from UI (lesson-data.json)

All chapter and quiz data lives in `lesson-data.json`, loaded by `index.html` via `fetch()` at runtime. The UI template is reusable across videos; data files are diff-friendly.

### Multi-language subtitle naming (MANDATORY)

Use the language name as the file suffix: `subtitles_en.vtt`, `subtitles_nl.vtt`. **Do not use compound suffixes** like `subtitles_en-nl.vtt` — it looks strange in the UI toggle and creates confusion. `lesson-data.json` `subtitleLangs` should list the base language name directly: `["en", "nl"]`.

**Dutch (`nl`) subtitles are MANDATORY for every lesson.** If Dutch subtitles are not available from YouTube, you MUST generate them via translation. A lesson without Dutch subtitles is incomplete — stop and fix before handing to the user. This is the single most common failure mode: the agent downloads English subtitles and considers the task done, leaving the user with a broken experience in a Dutch-language context.

### Adaptive translation chunk sizing

| Video length | Chunk size | Notes |
|---|---|---|
| Short (< 10 min, < 100 cues) | 20 | Default works fine |
| Medium (10–30 min, 100–400 cues) | 20 | Default; sequential processing |
| Long (30+ min, 400–800+ cues) | 20 | Default; sequential processing; takes longer |

Always use **1 subagent at a time** (not parallel). Sequential is faster on local models and avoids server overload.

### PDF generation: define `story` before `doc.build()`

A common error: defining the doc template, then defining `story`, then calling `doc.build(story)` — or worse, defining helper functions (`add_page_number`) **after** the content they should wrap. Always define `story` list, content, and page number callbacks **before** calling `doc.build()`.

### PDF page numbering

For documents with 15+ pages, always add page numbers using `onFirstPage` and `onLaterPages` callbacks in `doc.build()`.

**Better yet, always add page numbers to every PDF** — even short ones. Use `BaseDocTemplate` with a `PageTemplate` and `onPage` callback:

```python
from reportlab.platypus import BaseDocTemplate, PageTemplate

def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.HexColor('#999999'))
    page_num = canvas.getPageNumber()
    canvas.drawCentredString(A4[0]/2, 1*cm, f'Pagina {page_num}')
    canvas.restoreState()

doc = BaseDocTemplate(output_file, pagesize=A4)
doc.addPageTemplates([PageTemplate(id='main', frames=frame, onPage=add_page_number)])
doc.build(story)
```

### PDF `pdfFilename` must be set in lesson-data.json

When generating a PDF, always add `"pdfFilename"` to `lesson-data.json` alongside `pdfAvailable: true`. The sidebar download link in the template uses `data.pdfFilename` as its `href`. Without this field, the PDF download button is visible but dead — clicking it does nothing.

```json
{
  "pdfAvailable": true,
  "pdfFilename": "samenvatting_<slug>.pdf"
}
```

### HTTP server: instruct the user, don't start it yourself

The agent should **not** start the HTTP server. It should provide clear instructions at the end of the task so the user can start it on their own machine.

## Patterns Used Across Examples

### Template usage (CRITICAL)

**The file `extensions/lesson-template.html` is the single source of truth for the UI.**

When building a lesson, **always copy `extensions/lesson-template.html` into the project folder as `index.html`**. Never write HTML from scratch. The template contains all Vue 3 in-DOM fixes (lowercase state, entity escaping, video sizing, subtitle bar placement). Any `index.html` not derived from this template is guaranteed to break.

### YouTube iframe API

- `onYouTubeIframeAPIReady` and `seekTo()` for timestamped navigation
- VTT subtitles parsed client-side; displayed in a dedicated `<div>` bar below the iframe synced via `requestAnimationFrame`
- Local HTTP server required — `file://` doesn't work with the YouTube iframe API

### Vue 3 via CDN

- Load from `https://unpkg.com/vue@3/dist/vue.global.js`
- Tailwind CSS from `https://cdn.tailwindcss.com`
- No build step, no npm

### Test suite

`test-vtt-parser.js` is a standalone, dependency-free test suite loadable in any browser. It covers:
1. VTT parser correctness (rolling captions, CRLF, dedup, `>>` markers, entity decoding, short cue filtering)
2. Subtitle sync (mock `getCurrentTime()` against known cue boundaries)
3. Quiz shuffle statistics (100+ runs verify even distribution of correct answer index)
4. `lesson-data.json` structure validation (required fields, types, constraints)

## Example

### `examples/Barbara-Liskov/`

A complete interactive lesson built from a 35-minute interview with Barbara Liskov (Turing Award winner). Demonstrates all features including PDF generation.

**Architecture (split data/UI):**

- `lesson-data.json` — chapters, quiz, video metadata (data layer)
- `index.html` — Vue 3 + Tailwind CSS from CDN (UI template, loads data via `fetch()`)
- `subtitles_{en,nl}.vtt` — Clean WebVTT files (849 cues each)
- `samenvatting_barbara_liskov.pdf` — Dutch PDF summary with detailed chapter explanations

### `tests/`

- `test-vtt-parser.js` — Standalone test suite. Open in any browser — no server needed.

## Skills

### `youtube-interactive-lesson` skill

Invoked via `/youtube-interactive-lesson`. Given a YouTube URL, builds a complete interactive lesson page with synced subtitles, chapter navigation, and quiz. Full instructions — including hard-won lessons about Vue 3 gotchas, video sizing, and subtitle parsing — are in `.pi/skills/youtube-interactive-lesson/SKILL.md`.

Post-processes the downloaded `.vtt` file with Python to strip HTML tags, resolve XML entities, and deduplicate repeated lines. Translates subtitles by spawning subagents — **one at a time**, with disk-based checkpointing via `translations.json`.

**Dependency:** `yt-dlp` and `reportlab` — auto-installs if missing.
