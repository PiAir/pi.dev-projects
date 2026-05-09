---
name: youtube-interactive-lesson
description: Build a complete interactive educational HTML page from a YouTube video URL. Downloads transcript, translates to Dutch and English, generates chapters, subtitle overlay, and quiz. Use when the user provides a YouTube URL and wants an interactive lesson page.
allowed-tools: Bash,Read,Write,Edit
---

# YouTube Interactive Lesson Builder

## Invocation

```
/pi youtube-interactive-lesson <YouTube URL> [-- langs en,nl -- chunk-size 20 -- quizzes 8 -- map: My-Lesson, webserver poort: <port>, --pdf]
```

- `map` — subfolder name to create (default: derived from video title)
- `webserver poort` — local HTTP server port (default: 8765)
- `--pdf` — also generate a Dutch PDF summary (`samenvatting_<slug>.pdf`)
- `--langs <list>` — comma-separated target languages (default: en,nl)
- `--chunk-size <n>` — lines per translation subagent chunk (default: 20; increase for faster models)
- `--quizzes <n>` — number of quiz questions (default: 8)
- `--concepts <n>` — number of key concepts to extract for two-pass quiz (default: 10)

Example: `/pi youtube-interactive-lesson https://www.youtube.com/watch?v=XYZ -- map: My-Lesson, langs en,de -- chunk-size 50 -- pdf`

---

Given a YouTube URL, this skill produces a self-contained `index.html` with:
- Sidebar chapter navigation with topic timestamps
- Video player (YouTube iframe API)
- Synced subtitle bar (multi-language toggle)
- Tabbed detail view per chapter (description + key points)
- Shuffled multiple-choice quiz with feedback and clip links

## Step 1 — Create the project folder

**First, copy the template:**

```
cp extensions/lesson-template.html <subfolder>/index.html
```

```
<subfolder>/
  index.html              ← COPY of extensions/lesson-template.html (never write from scratch!)
  lesson-data.json        # chapters, quiz, timestamps (data layer)
  transcript.en.vtt       ← raw download, not served
  gen_nl_vtt.py           ← generates subtitle VTT files
  subtitles_en.vtt
  subtitles_en-de.vtt     ← one per target language pair
  gen_pdf.py              ← PDF generator (if --pdf)
  samenvatting_<slug>.pdf ← generated PDF (if --pdf)
  test-vtt-parser.js      ← automated VTT parser tests
```

`index.html` loads `lesson-data.json` at runtime via `fetch()`. Only `index.html`, `lesson-data.json`, the `.vtt` files, and optional `.pdf` are needed to view the lesson.

## Step 2 — Download subtitles

Download the best available subtitle track using this priority order:

1. `en` or `en-en` — English (manual or auto-generated)
2. The primary language available in `--langs`
3. `nl` — Dutch manual subtitles (fallback)

**Never request `nl-en`** (YouTube's auto-translated Dutch). YouTube returns HTTP 429 for auto-translated tracks without browser cookies. Manual tracks (`en`, `nl`) download fine.

**PowerShell:** Write download commands to `.py` scripts — do not use long one-liners in PowerShell.

```powershell
# Create download script first
# Then run it
```

Call `yt-dlp` via Python to ensure cross-platform compatibility:

```bash
# Create a download script
python -m yt_dlp --write-auto-sub --write-subs --sub-langs "en,en-en,nl" --skip-download --output "transcript" "YOUTUBE_URL"

# Auto-install if missing
pip install yt-dlp -q
```

Check which file was created: if `transcript.en.vtt` exists, use that as the base. If only a non-English track exists, use that as the base and translate to English plus any additional target languages in Step 3.

## Step 3 — Generate clean subtitle VTT files

YouTube auto-captions use a **rolling format**: each cue block contains the previous line plus one new word/phrase, with inline `<HH:MM:SS.mmm><c>` word-timing tags. Parse this with Python, not a regex split:

**Algorithm:**
1. Split on blank lines (`\n\n+`) — use `re.split` on the raw text
2. For each block, find the `-->` line to get start/end timestamps
3. Strip all `<tag>` content (word-timing tags, `<c>`, etc.)
4. Decode HTML entities: `&amp;` → `&`, `&gt;` → `>`, `&lt;` → `<`
5. From the remaining text lines, take **only the last line** — that is the currently-spoken sentence
6. Skip cues shorter than 0.05 s (they are transition artifacts)
7. Deduplicate: if two consecutive cues have identical text, extend the first cue's end time instead of emitting a duplicate

This yields clean, correctly-timed display cues (typically 400–600 for a 20-minute video).

**CRITICAL — line endings:** VTT files downloaded from YouTube may have CRLF (`\r\n`) or LF (`\n`) line endings depending on platform. The blank-line separator between cues must be normalized. Always normalise before parsing to handle both Windows and Unix line endings:

```python
content = content.replace('\r\n', '\n').replace('\r', '\n')
```

If you skip this step, `re.split(r'\n\n+', content)` may treat the entire file as one block (on Windows with CRLF), and every cue gets joined into a single massive string — all subtitles appear simultaneously.

### Multi-language subtitle naming (MANDATORY)

Use the language name as the file suffix: `subtitles_en.vtt`, `subtitles_nl.vtt`. **Do NOT use compound suffixes** like `subtitles_en-nl.vtt`. It looks strange in the UI toggle and creates confusion.

`lesson-data.json` `subtitleLangs` must list the base language names directly: `["en", "nl"]`.

**Dutch (`nl`) subtitles are MANDATORY.** A lesson without Dutch subtitles is **incomplete**. If Dutch subtitles are not available from YouTube, generate them via translation before producing `lesson-data.json`. The `subtitleLangs` field in `lesson-data.json` must always include `"nl"`.

**Example:** `--langs en,de,ja` produces:
- `subtitles_en.vtt` (base track)
- `subtitles_en-de.vtt`
- `subtitles_en-ja.vtt`

Note: even in this example, Dutch must be added: `subtitles_nl.vtt` is always produced.

### Translation with adaptive chunk sizing (Suggestion 2)

**CRITICAL — Never hardcode translations as a Python dict.** A video has 400–800 subtitle cues. Writing them by hand in one pass is impossible; the model will stop partway and leave the rest untranslated.

**CRITICAL — Never translate via an external Python script.** Any script that loops over hundreds of cues making API calls will hit the agent tool timeout before it finishes. The result is a silently truncated translation file — no error, just missing subtitles.

**REQUIRED — Translate using subagents with disk-based checkpointing:**

Translation can take a long time on slower models (4–10 minutes per chunk). The protocol below ensures no work is lost if the session stalls, and prevents the model from abandoning the approach mid-way.

**Before starting, write `translations.json` to disk** as an empty object `{}`. After each chunk is translated, merge the result into `translations.json` immediately. This means a restart only needs to redo untranslated chunks — already-completed work is never lost.

**Adaptive chunk sizing:** The `--chunk-size` parameter sets the initial chunk size, but the skill should auto-tune based on model speed:

| Model speed | Initial chunk | Parallelism | Tuning logic |
|---|---|---|---|
| Slow local (< 50 s/chunk) | 20 | 1 at a time | Start small, double if < 30s, cap at 50 |
| Fast local (10–30 s/chunk) | 30 | 1 at a time | Start at default, increase if < 20s per line |
| Cloud API (< 5 s/chunk) | 100 | 5 at a time | Start high, reduce if rate-limited |

The skill should measure the first chunk's elapsed time and adjust:
```python
import time, json

# After first chunk:
elapsed = end_time - start_time
if elapsed < 15:
    chunk_size = min(chunk_size * 2, 100)  # double, cap at 100
elif elapsed > 60:
    chunk_size = max(chunk_size // 2, 10)  # halve, floor at 10
```

**Chunk size: 20 lines** (not 50) as default. Smaller chunks finish faster per subagent call, which reduces the chance that a slow model times out or abandons the task mid-chunk.

**Concurrency: 1 subagent at a time** (not 5 in parallel). On a slow local model, 5 parallel requests compete for the same GPU, making each one slower. Sequential processing is faster overall and avoids server overload.

**Protocol:**

1. After parsing all display cues, collect the list of unique texts (from the base language).
2. Check whether `translations.json` already exists and load it. Any lines already present can be skipped.
3. Split the **untranslated** lines into chunks using the current `chunk_size`.
4. For each chunk (one at a time, in order):
   a. Spawn one subagent with this exact task:

      > Translate the following subtitle lines from {source} to {target}. Return ONLY a valid JSON object mapping each source line exactly to its {target} translation. No markdown, no explanation, no code block — just the raw JSON object.
      > Lines: `["line 1", "line 2", ...]`

   b. Parse the subagent's JSON response.
   c. Merge the result into `translations.json` on disk immediately. **Do not wait until all chunks are done.**
   d. Log progress: `Chunk N/M done — X lines translated so far.`
5. After all chunks for this language pair are complete, write the `.vtt` file.
6. Repeat steps 2–5 for each additional target language.

**If a chunk's response cannot be parsed as JSON**, log the error and move on to the next chunk. Missing lines will display the original text as fallback — this is acceptable. Do not retry, do not abandon the whole translation.

**Do not switch strategy if a chunk takes longer than expected.** Slow progress is normal for a 35-minute video on a local model. Stay the course: one chunk at a time, save to disk, continue.

Example disk-save after each chunk (Python):
```python
import json, os

cache_path = 'translations.json'

# Load existing cache
if os.path.exists(cache_path):
    with open(cache_path, encoding='utf-8') as f:
        translations = json.load(f)
else:
    translations = {}
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(translations, f)

# After each subagent returns chunk_result (dict):
translations.update(chunk_result)
with open(cache_path, 'w', encoding='utf-8') as f:
    json.dump(translations, f, ensure_ascii=False, indent=2)
```

**Speaker-change markers:** YouTube uses `>>` to indicate a new speaker. Strip these from the display text:

```python
clean = re.sub(r'^>>\s*', '', text).strip()
```

Also handle `>> text >> text` (multiple speakers in one cue):

```python
clean = re.sub(r'\s*>>\s*', ' ', clean).strip()
```

### UTF-8 encoding: always use ensure_ascii=False for JSON, explicit UTF-8 for VTT

When JSON data files contain non-ASCII characters (Dutch accented letters like é, ë, ö), Python's `json.dump` **default `ensure_ascii=True` will escape them as `\u00e9` etc.** If these are then written with a different encoding or read back incorrectly, the result is **mojibake**: `Ã©` instead of `é`, `â€"` instead of `—`, `Ã«` instead of `ë`. This is a common silent corruption that makes subtitle text unreadable in any editor.

**Always use `ensure_ascii=False` and explicit `encoding='utf-8'` when writing JSON data files:**

```python
import json

# WRONG — escapes non-ASCII, risking mojibake:
json.dump(data, f, ensure_ascii=True)   # default!

# CORRECT — write actual UTF-8 characters:
json.dump(data, f, ensure_ascii=False, indent=2)
```

**Always write with explicit `'w', encoding='utf-8'` for VTT files** — on Windows, `open('file', 'r')` uses `cp1252` by default, not UTF-8:

```python
with open('subtitles_nl.vtt', 'w', encoding='utf-8') as f:
    f.write(content)
```

**In the browser, always use `TextDecoder('utf-8')` + `arrayBuffer()` instead of `res.text()`** to avoid any codepage ambiguity in the fetch response:

```javascript
const buf = await res.arrayBuffer();
const text = new TextDecoder('utf-8').decode(buf);
```

**Verify before handing to user:** Open JSON/VTT files in any editor that supports UTF-8. If you see `Ã©` or `â€"` or `Ã«` anywhere, the file is corrupted.

## Step 4 — Build index.html and lesson-data.json

### CRITICAL: Start from the template

**`extensions/lesson-template.html` IS the `index.html` template.** Copy it verbatim into the project folder as `index.html`. Never write HTML from scratch — the template contains all Vue 3 in-DOM fixes (lowercase state, entity escaping, video sizing, subtitle bar placement). Writing from scratch is the #1 cause of broken lessons.

After copying the template, the only differences between lessons are the DATA in `lesson-data.json`. Do not modify the template's HTML structure, CSS, or JavaScript logic.

### Architecture change: split data from UI (Suggestion 4)

Instead of embedding all chapters and quiz data in `index.html`, split into two files:

- **`lesson-data.json`** — chapters, quiz questions, video ID, available subtitle languages
- **`index.html`** — UI template (Vue 3 + Tailwind CSS), loads `lesson-data.json` via `fetch()`

This means:
- Quiz/chapters can be regenerated without touching the UI template
- The HTML template is reusable across different videos
- Data files are diff-friendly; the template stays stable

### Technology stack

- **Vue 3** via CDN (`https://unpkg.com/vue@3/dist/vue.global.js`)
- **Tailwind CSS** via CDN (`https://cdn.tailwindcss.com`)
- **No build step**, no npm, no bundler

### Data layer (lesson-data.json) structure

```json
{
  "videoId": "abc123",
  "videoTitle": "Video Title",
  "subtitleLangs": ["en", "en-de"],
  "chapters": [...],
  "quiz": [...],
  "pdfAvailable": true,
  "pdfFilename": "samenvatting_<slug>.pdf"
}
```

**NOTE:** `pdfFilename` is **required** when `pdfAvailable` is `true`. The sidebar PDF download link uses `data.pdfFilename` as its `href`. Without it, the button is visible but clicking does nothing.

### UI layer (index.html) — load data dynamically

```javascript
// In the Vue setup function:
const DATA_URL = 'lesson-data.json';

// Load data at mount time
const { createApp, ref, computed, onMounted } = Vue;

createApp({
  setup() {
    const data = ref(null);

    onMounted(async () => {
      try {
        const resp = await fetch(DATA_URL);
        data.value = await resp.json();
      } catch (e) {
        console.error('Failed to load lesson data:', e);
      }
    });

    // All state derived from data.value
    const chapters = computed(() => data.value?.chapters || []);
    const questions = computed(() => data.value?.quiz || []);
    const subtitleLangs = computed(() => data.value?.subtitleLangs || []);
    const videoId = computed(() => data.value?.videoId || '');
    // ... etc
  }
}).mount('#app');
```

### CRITICAL: Vue 3 in-DOM template — camelCase variable names

This is the single most important gotcha. Vue 3 in-DOM templates (HTML parsed by the browser before Vue compiles it) **lowercase all identifiers** in the compiled output. `quizQuestions` becomes `quizquestions`, `selectedAnswer` becomes `selectedanswer`, etc.

**Rule: all reactive state returned from `setup()` must use only lowercase names.**

```javascript
// WRONG — will silently break after the first reactive update:
const activeChapter = ref(0);
const quizQuestions = ref([]);
const selectedAnswer = ref(null);

// CORRECT:
const chapter = ref(0);
const questions = ref([]);
const answer = ref(null);
```

The failure mode is subtle: the component renders fine on first load (Vue resolves the names before HTML parsing), but after a reactive update (e.g. clicking a quiz answer), Vue re-renders using the lowercased names, finds them undefined, throws a silent error, and the DOM stops updating. The user sees the click do nothing.

Also rename loop variables that collide with state: use `v-for="t in tabs"` not `v-for="tab in tabs"` if `tab` could conflict.

### Video sizing

**Goal:** video takes roughly the top third of the viewport; aspect ratio is always 16:9; no cropping.

**Correct approach — set height, derive width from aspect-ratio:**

```css
#player-wrapper {
  position: relative;
  height: 42vh;
  aspect-ratio: 16 / 9;
  max-width: 100%;
}
#player-wrapper iframe,
#player-wrapper > div {
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 100%;
  border: 0;
}
```

**Do NOT use `max-height` + `aspect-ratio` together.** When both are set, `max-height` clips the element's height without adjusting the width, producing a stretched or letterboxed video that does not match the 16:9 ratio.

Pass explicit dimensions to the YouTube API constructor so it does not default to 640×390:

```javascript
player = new YT.Player('yt-player', {
  videoId: VIDEO_ID,
  width: '100%',
  height: '100%',
  ...
});
```

### Layout structure

Full-viewport flexbox with no outer scroll. The video column (player + subtitle bar + tabs + content) must be constrained to the exact width of the video — otherwise the subtitle bar and tab content span the full remaining window width, which looks bad on wide screens.

**Key principle:** set an explicit `width: calc(42vh * 16 / 9)` on `#video-col` so the column is always exactly as wide as the video. Do NOT use `width: fit-content` — child elements with `width: 100%` (e.g. `#content-area`) will expand to fill `#main` and break the constraint.

```css
html, body { height: 100%; margin: 0; }
#app        { display: flex; height: 100vh; overflow: hidden; }
#sidebar    { width: 280px; min-width: 280px; display: flex; flex-direction: column; height: 100%; }
#main       { flex: 1; display: flex; flex-direction: column; overflow: hidden; min-width: 0; min-height: 0;
              align-items: flex-start; }
#video-col  { display: flex; flex-direction: column;
              width: calc(42vh * 16 / 9); max-width: 100%;
              height: 100%; min-height: 0; }
#video-area { flex-shrink: 0; background: #000; width: 100%; }
#player-wrapper { position: relative; height: 42vh; width: 100%; }
#content-area { flex: 1; min-height: 0; display: flex; flex-direction: column; overflow: hidden; }
#tab-content  { flex: 1; overflow-y: auto; padding: 20px 24px; }
```

HTML structure — `#video-col` wraps everything to the right of the sidebar:

```html
<div id="main">
  <div id="video-col">
    <div id="video-area">
      <div id="player-wrapper">
        <div id="yt-player"></div>
      </div>
      <div id="subtitle-bar">...</div>
    </div>
    <div id="content-area">
      <div id="tab-bar">...</div>
      <div id="tab-content">...</div>
    </div>
  </div>
</div>
```

`min-height: 0` on flex children is required to allow them to shrink below their content size. Without it, `#content-area` will grow past the viewport and the layout breaks.

The `42vh` in `calc(42vh * 16 / 9)` matches the `height: 42vh` set on `#player-wrapper` — if you change the video height, update both values together.

### Subtitle bar

**Do not overlay subtitles on top of the YouTube iframe.** iframes block pointer events and CSS stacking context makes overlays unreliable.

Instead, place a dedicated subtitle bar **below** the video wrapper as a sibling element inside `#video-area`. It inherits the exact video width from `#video-col`, so subtitles are centred under the image rather than over the full window width:

```html
<div id="video-area">
  <div id="player-wrapper">
    <div id="yt-player" style="width:100%;height:100%;"></div>
  </div>
  <div id="subtitle-bar">
    <span class="sub-text">{{subtitle || '&nbsp;'}}</span>
  </div>
</div>
```

```css
#subtitle-bar {
  background: #111;
  min-height: 2.6rem;
  display: flex; align-items: center; justify-content: center;
  padding: 6px 16px;
}
```

The subtitle loop uses `requestAnimationFrame` and reads `player.getCurrentTime()` to find the active cue:

```javascript
function tick() {
  if (player && typeof player.getCurrentTime === 'function' && sublang.value !== 'off') {
    const t = player.getCurrentTime();
    const langKey = sublang.value; // 'en', 'en-de', etc.
    const cue = subtitles[langKey].find(c => t >= c.start && t < c.end);
    subtitle.value = cue ? cue.text : '';
  }
  rafId = requestAnimationFrame(tick);
}
```

Start the loop inside `onReady`:
```javascript
events: { onReady: () => { rafId = requestAnimationFrame(tick); } }
```

### Multi-language subtitle toggle

The language toggle in the sidebar is now **dynamic** — it reads `subtitleLangs` from `lesson-data.json`:

```html
<div v-if="data" class="lang-toggle">
  <button class="lang-btn" :class="{active: sublang===lang}" 
          v-for="lang in data.subtitleLangs" :key="lang"
          @click="sublang=lang">
    {{ lang.toUpperCase() }}
  </button>
  <button class="lang-btn" :class="{active: sublang==='off'}" 
          @click="sublang='off'">
    Uit
  </button>
</div>
```

### VTT parser in the browser

The fetched VTT file also has CRLF line endings — normalise before parsing, for the same reason as in Step 3:

```javascript
function parseVTT(text) {
  const cues = [];
  const normalised = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
  for (const block of normalised.split(/\n\n+/)) {
    const lines = block.trim().split('\n');
    const tsLine = lines.find(l => l.includes('-->'));
    if (!tsLine) continue;
    const [s, e] = tsLine.split('-->').map(p => toSec(p.trim().split(' ')[0]));
    const txt = lines
      .filter(l => l && !l.includes('-->') &&
        !/^(WEBVTT|NOTE|Kind:|Language:)/.test(l) &&
        !/^\d+$/.test(l.trim()))
      .join(' ').trim();
    const clean = txt.replace(/^>>\s*/g, '').replace(/\s*>>\s*/g, ' ').trim();
    if (clean) cues.push({ start: s, end: e, text: clean });
  }
  return cues;
}
```

### HTML entities in Vue template expressions

The `>` character inside `{{ }}` expressions is treated as an HTML tag close by the browser parser, corrupting the template. Use HTML entities or move the arrow outside the expression:

```html
<!-- WRONG — browser parses > as closing a tag: -->
{{qidx < questions.length-1 ? 'Volgende →' : 'Resultaten'}}

<!-- CORRECT: -->
<span v-if="qidx < questions.length-1">Volgende &rarr;</span>
<span v-else>Resultaten</span>
```

The same applies to `<` — prefer `v-if`/`v-else` over ternaries with comparison operators inside mustaches.

### Quiz design — two-pass generation (Suggestion 3)

Instead of generating questions directly from raw subtitle lines, use a **two-pass approach**:

**Pass 1 — Concept extraction:** Ask the LLM to identify N key concepts from the full transcript. For each concept, require:
- A concept name
- A relevant timestamp range
- A brief description

**Pass 2 — Question generation:** For each extracted concept, generate a quiz question anchored to the timestamp range, using the chapter data as context:

```javascript
// lesson-data.json quiz entry:
{
  "concept": "Data-abstractie",
  "question": "Wat is het centrale idee van data-abstractie dat Liskov ontwikkelde?",
  "options": [...],
  "correct": 0,
  "explanation": "...",
  "clipTime": 359,
  "anchoredChapter": 2,
  "sourceLine": "subtitle line reference for verification"
}
```

**Quality heuristic:** Accept the question only if:
- The correct answer appears in at least 3 subtitle lines (not a throwaway detail)
- All 4 options are within 20% of each other in character length
- The `clipTime` falls within the concept's timestamp range

If a concept fails these checks, ask the LLM to regenerate that concept's question.

### Chapter data

Derive chapters from the transcript's natural structure. Each chapter needs:

```json
{
  "title": "Korte titel",
  "start": 128,
  "description": "Paragraaf die dit deel van de video samenvat.",
  "keyPoints": ["Punt 1", "Punt 2", "Punt 3", "Punt 4"],
  "topics": [{"label": "Deelonderwerp", "start": 145}]
}
```

### Serving locally

The YouTube iframe API requires an HTTP origin (not `file://`). Always start a local server before testing:

```powershell
# From inside the project subfolder
python -m http.server <port>

# Or in background
Start-Sleep -Infinity  # keep terminal open
```

Then open `http://localhost:<port>/` in your browser.

## Step 5 — PDF summary (optional, required when `--pdf` is passed)

Generate a Dutch PDF summary file `samenvatting_<slug>.pdf` in the project folder using **reportlab**.

### Install dependency

```bash
pip install reportlab -q
```

### What the PDF must contain

- **Title page**: video title, subtitle "Uitgebreide samenvatting", source URL
- **Short intro paragraph** explaining the document structure
- **One section per chapter**, each with:
  - Chapter title + timecode (formatted as `m:ss`)
  - Description paragraph (2–4 sentences)
  - Key points (bullet list)
  - Per topic: topic label + timecode as subheading, followed by a detailed paragraph (~100 words) of toelichting in Dutch
- **Footer line** with generation note

Use the same `chapters` data from `lesson-data.json` — descriptions, key points and topic labels are already defined there. For the per-topic toelichting paragraphs, write them based on the transcript content (you have already read the transcript at this point).

### ReportLab styles to use

```python
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
```

### Write the script as `gen_pdf.py`

Write the full Python script as a file `gen_pdf.py` in the project folder, then run it:

```bash
python gen_pdf.py
```

### Sidebar download button

After generating the PDF, set `pdfAvailable: true` in `lesson-data.json` and add a download link in the sidebar of `index.html`.

---

## Step 6 — Automated tests (Suggestion 5)

Write `test-vtt-parser.js` — a dependency-free test file loadable in any browser. It covers three areas:

### Test 1: VTT parser correctness

Tests the browser's `parseVTT()` function:
- Rolling caption deduplication (consecutive identical lines)
- CRLF line ending handling
- `>>` speaker marker stripping
- HTML entity decoding
- Short cue filtering (< 0.05s)
- Header/metadata line skipping

```javascript
// test-vtt-parser.js
(function() {
  let passed = 0, failed = 0;

  function assert(cond, msg) {
    if (cond) { passed++; console.log('✓', msg); }
    else { failed++; console.error('✗', msg); }
  }

  function parseVTT(text) {
    // Same implementation as in index.html
    ...
  }

  // Test: rolling captions should deduplicate
  const vttRolling = 'WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nHello\n\n00:00:02.000 --> 00:00:03.000\nHello world';
  const cuesRolling = parseVTT(vttRolling);
  assert(cuesRolling.length === 2, 'rolling captions: 2 cues (not deduped yet, just checking count)');
  assert(cuesRolling[1].text === 'Hello world', 'rolling captions: second cue has full text');

  // Test: CRLF handling
  const vttCRLF = 'WEBVTT\r\n\r\n00:00:01.000 --> 00:00:03.000\nHello world';
  const cuesCRLF = parseVTT(vttCRLF);
  assert(cuesCRLF.length === 1, 'CRLF: still parses to 1 cue');

  // Test: >> marker stripping
  const vttSpeaker = 'WEBVTT\n\n00:00:01.000 --> 00:00:03.000\n>> Speaker 1\nHello >> text >> there';
  const cuesSpeaker = parseVTT(vttSpeaker);
  assert(cuesSpeaker[0].text === 'Speaker 1 Hello text there'.trim(), '>> markers stripped');

  // Test: short cue filtering
  const vttShort = 'WEBVTT\n\n00:00:01.000 --> 00:00:01.020\nHi';
  const cuesShort = parseVTT(vttShort);
  assert(cuesShort.length === 0, 'short cues (< 0.05s) filtered out');

  // Summary
  const div = document.createElement('div');
  div.innerHTML = `Tests: ${passed} passed, ${failed} failed`;
  document.body.appendChild(div);
  console.log(`Total: ${passed} passed, ${failed} failed`);
})();
```

### Test 2: Subtitle sync

Mock `player.getCurrentTime()` and verify the active cue updates correctly:

```javascript
// Test: subtitle sync
function testSync() {
  const subtitles = parseVTT(vttData);
  const testTimes = [0.5, 1.5, 2.5, 3.5, 5.0];
  // ... verify each time returns the expected cue
}
```

### Test 3: Quiz shuffle

Run shuffle 100 times and verify the correct answer moves to a new index:

```javascript
// Test: quiz shuffle statistics
function testShuffle() {
  const options = ['A', 'B', 'C', 'D'];
  const correctText = 'C';
  let uniqueIndices = new Set();
  
  for (let i = 0; i < 100; i++) {
    const shuffled = shuffle(options);
    const correctIdx = shuffled.indexOf(correctText);
    uniqueIndices.add(correctIdx);
  }
  
  // With 4 options, should appear in at least 3 different indices
  assert(uniqueIndices.size >= 3, 'shuffle distributes correct answer (expected >= 3 unique indices, got ' + uniqueIndices.size + ')');
  // With 4 options, should appear in all 4 indices (statistically certain over 100 runs)
  assert(uniqueIndices.size >= 3, 'shuffle reaches all positions');
}
```

Run tests by opening `test-vtt-parser.js` in a browser with the project's `index.html` (so `parseVTT` is available). The test writes results to the console and a visible DOM element.

## Step 7 — Quality checklist before handing to the user

- [ ] Video displays at correct 16:9 ratio, not stretched or cropped
- [ ] Subtitle bar and tab content are constrained to the video column width (not full window width)
- [ ] Subtitle bar shows one line at a time, synced to video playback
- [ ] No `>>` speaker markers visible in subtitles
- [ ] Clicking a chapter in the sidebar seeks the video and opens the detail tab
- [ ] Quiz options are all similar in length (no obvious length giveaway)
- [ ] After answering, feedback box appears and buttons change colour
- [ ] "Volgende" / "Resultaten" button works through all questions
- [ ] Score screen appears after the last question
- [ ] "Opnieuw proberen" reshuffles questions and options
- [ ] No Vue warnings in the browser console
- [ ] `lesson-data.json` exists and is valid JSON
- [ ] Language toggle dynamically shows available subtitle languages
- [ ] `test-vtt-parser.js` passes all tests (check browser console)
- [ ] (if --pdf) `samenvatting_*.pdf` exists in the project folder and is non-empty
- [ ] (if --pdf) Sidebar shows "Samenvatting (PDF)" download button
- [ ] (if --pdf) All chapter timecodes in the PDF match those in `lesson-data.json`

---

## Windows / PowerShell Notes

- **Write Python commands to `.py` scripts** — never use long one-liners in PowerShell
- **Subagent commands**: Use the `Bash` tool (which uses bash, not PowerShell) for Python scripts
- **For HTTP server**: `python -m http.server <port>` works from either bash or PowerShell
- **File paths**: Use forward slashes `/` in all tool calls for cross-platform compatibility
