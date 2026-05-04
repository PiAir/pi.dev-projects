---
name: youtube-interactive-lesson
description: Build a complete interactive educational HTML page from a YouTube video URL. Downloads transcript, translates to Dutch and English, generates chapters, subtitle overlay, and quiz. Use when the user provides a YouTube URL and wants an interactive lesson page.
allowed-tools: Bash,Read,Write,Edit
---

# YouTube Interactive Lesson Builder

## Invocation

```
/youtube-interactive-lesson <YouTube URL> [-- map: <folder>, webserver poort: <port>, --pdf]
```

- `map` — subfolder name to create (default: derived from video title)
- `webserver poort` — local HTTP server port (default: 8765)
- `--pdf` — also generate a Dutch PDF summary (`samenvatting_<slug>.pdf`) and add a download button to the sidebar

Example: `/youtube-interactive-lesson https://www.youtube.com/watch?v=XYZ -- map: My-Lesson, webserver poort: 8787, --pdf`

If the user asks for a PDF summary after the lesson page is already built, follow Step 5 directly.

---

Given a YouTube URL, this skill produces a self-contained `index.html` with:
- Sidebar chapter navigation with topic timestamps
- Video player (YouTube iframe API)
- Synced subtitle bar (Dutch + English toggle)
- Tabbed detail view per chapter (description + key points)
- Shuffled multiple-choice quiz with feedback and clip links

## Step 1 — Create the project folder

```
<subfolder>/
  index.html
  transcript.en.vtt        ← raw download, not served
  gen_nl_vtt.py            ← generates subtitles_en.vtt + subtitles_nl.vtt
  subtitles_en.vtt
  subtitles_nl.vtt
```

## Step 2 — Download subtitles

Download the best available subtitle track using this priority order:

1. `en` or `en-en` — English (manual or auto-generated)
2. `nl` — Dutch manual subtitles (only if no English is available)

**Never request `nl-en`** (YouTube's auto-translated Dutch). YouTube returns HTTP 429 for auto-translated tracks without browser cookies. Manual tracks (`en`, `nl`) download fine.

Call `yt-dlp` via Python to ensure cross-platform compatibility:

```bash
# Works on Windows, Linux, macOS, WSL2
python -m yt_dlp --write-auto-sub --write-subs --sub-langs "en,en-en,nl" --skip-download --output "transcript" "YOUTUBE_URL"

# On some systems you may need python3:
python3 -m yt_dlp --write-auto-sub --write-subs --sub-langs "en,en-en,nl" --skip-download --output "transcript" "YOUTUBE_URL"
```

If `yt-dlp` is not installed, the skill will auto-install it:
```bash
pip install yt-dlp
# or: pip3 install yt-dlp
```

Check which file was created: if `transcript.en.vtt` exists, use that as the base. If only `transcript.nl.vtt` exists, use that and translate to English in Step 3 (reversing the direction).

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

**Translation:** Build a Python dict mapping each English display line to its Dutch translation. Translate all unique lines, then write both `subtitles_en.vtt` and `subtitles_nl.vtt` with identical timestamps:

```
WEBVTT
Kind: captions
Language: nl

00:00:00.080 --> 00:00:01.429
Nederlandse tekst hier
```

If only Dutch is available (no English), translate to English instead. If neither language is available, use whatever is available as the base and translate both directions.

**CRITICAL — Never hardcode translations as a Python dict.** A video has 400–800 subtitle cues. Writing them by hand in one pass is impossible; the model will stop partway and leave the rest untranslated.

**CRITICAL — Never translate via an external Python script.** Any script that loops over hundreds of cues making API calls will hit the agent tool timeout before it finishes. The result is a silently truncated translation file — no error, just missing subtitles.

**REQUIRED — Translate using subagents, max 5 at a time:**

1. After parsing all display cues, collect the list of unique English texts.
2. Split into chunks of 50 lines.
3. Process chunks in groups of **at most 5**, spawning one subagent per chunk in the group. Wait for all 5 to complete before starting the next group.
4. Each subagent receives this task:

   > Translate the following subtitle lines from English to Dutch. Return ONLY a JSON object mapping each source line exactly to its Dutch translation. No markdown, no commentary.
   > `["line 1", "line 2", ...]`

   The subagent returns the JSON object directly as its response.

5. Parse each subagent's JSON response and merge into a single `translations` dict.
6. Write `subtitles_nl.vtt` using the merged dict.

The 5-at-a-time cap avoids overloading the local LLM server. Each subagent handles its own translation directly — no Python API calls needed.

**Speaker-change markers:** YouTube uses `>>` to indicate a new speaker. Strip these from the display text:

```python
clean = re.sub(r'^>>\s*', '', text).strip()
```

Also handle `>> text >> text` (multiple speakers in one cue):

```python
clean = re.sub(r'\s*>>\s*', ' ', clean).strip()
```

## Step 4 — Build index.html

### Technology stack

- **Vue 3** via CDN (`https://unpkg.com/vue@3/dist/vue.global.js`)
- **Tailwind CSS** via CDN (`https://cdn.tailwindcss.com`)
- No build step, no npm, no bundler

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
    const cue = subtitles[sublang.value].find(c => t >= c.start && t < c.end);
    subtitle.value = cue ? cue.text : '';
  }
  rafId = requestAnimationFrame(tick);
}
```

Start the loop inside `onReady`:
```javascript
events: { onReady: () => { rafId = requestAnimationFrame(tick); } }
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

### Quiz design

**Question data structure:**

```javascript
{
  question: 'Vraagstelling?',
  options: ['Optie A', 'Optie B', 'Optie C', 'Optie D'],
  correct: 1,           // index into options
  explanation: 'Uitleg waarom het juiste antwoord juist is.',
  clipTime: 128         // seconds — null if no specific moment
}
```

**Shuffle both questions and options on load and on reset:**

```javascript
function shuffleOptions(q) {
  const correctText = q.options[q.correct];
  const opts = shuffle([...q.options]);
  return { ...q, options: opts, correct: opts.indexOf(correctText) };
}

const questions = ref(shuffle(allQ).map(shuffleOptions));
```

**Answer option length:** Write all four options at roughly equal length. The correct answer is often written with more detail because it needs to be unambiguous; this makes it identifiable by length alone. Extend the wrong answers with plausible but incorrect detail so all options are similar in length.

**Reactive state names (all lowercase):**

```javascript
const questions = ref(shuffle(allQ).map(shuffleOptions));
const qidx      = ref(0);
const answer    = ref(null);
const score     = ref(0);
const finished  = ref(false);
const pct       = computed(() => score.value / questions.value.length * 100);
const msg       = computed(() => { ... });
```

**Click handler guard** — prevents double-answering:

```javascript
function selectAnswer(oi) {
  if (answer.value !== null) return;
  answer.value = oi;
  if (oi === questions.value[qidx.value].correct) score.value++;
}
```

**Disabled buttons** use `:disabled="answer!==null"` — this works correctly because `answer` is already lowercase.

### Chapters

Derive 5–8 chapters by watching the video structure. Each chapter needs:

```javascript
{
  title: 'Korte titel',
  start: 128,           // seconds
  description: 'Paragraaf die dit deel van de video samenvat.',
  keyPoints: ['Punt 1', 'Punt 2', 'Punt 3', 'Punt 4'],
  topics: [{ label: 'Deelonderwerp', start: 145 }]
}
```

Use the transcript to identify natural breaks. Topic timestamps are clickable — they call `player.seekTo(t.start, true)`.

### Serving locally

The YouTube iframe API requires an HTTP origin (not `file://`). Always start a local server before testing:

```bash
# From inside the project subfolder (use the port from the invocation, default 8765):
python -m http.server <port>

# Alternative (if python points to Python 2):
python3 -m http.server <port>
```

Then open `http://localhost:<port>/` in your browser.

**Platform notes:**
- **Windows**: Use PowerShell or Command Prompt
- **Linux/macOS/WSL2**: Use any terminal
- Server runs in foreground; press `Ctrl+C` to stop

## Step 5 — PDF summary (optional, required when `--pdf` is passed)

Generate a Dutch PDF summary file `samenvatting_<slug>.pdf` in the project folder using **reportlab**.

### Install dependency

```bash
# Install reportlab (works on all platforms)
pip install reportlab -q

# On some systems you may need pip3:
pip3 install reportlab -q
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

Use the same `allChapters` data that drives `index.html` — descriptions, key points and topic labels are already defined there. For the per-topic toelichting paragraphs, write them based on the transcript content (you have already read the transcript at this point).

### ReportLab styles to use

```python
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable

# Key style settings (adjust colours to taste):
# - Title:          fontSize=22, color=#0f172a
# - Subtitle/meta:  fontSize=10, color=#64748b
# - Chapter heading: fontSize=14, color=#1e40af  (Heading1)
# - Topic heading:   fontSize=11, color=#0369a1  (Heading2)
# - Body text:       fontSize=10, leading=15, alignment=TA_JUSTIFY
# - Bullet items:    fontSize=10, leftIndent=14, prefix "• "
```

### Write the script as `gen_pdf.py`

Write the full Python script as a file `gen_pdf.py` in the project folder, then run it:

```bash
python gen_pdf.py
# or: python3 gen_pdf.py
```

Do **not** inline hundreds of translation strings or chapter data. The script reads `allChapters` data that you write into it directly (copy from `index.html`). The per-topic toelichting paragraphs are written as Python string literals in `gen_pdf.py`.

### Sidebar download button

After generating the PDF, add a download link at the bottom of the sidebar in `index.html`, just before `</div>` that closes `#sidebar`:

```html
<div style="padding: 10px 14px 14px; border-top: 1px solid #334155;">
  <a href="samenvatting_<slug>.pdf" target="_blank"
     style="display:flex;align-items:center;gap:8px;background:#1e40af;color:#e0f2fe;
            text-decoration:none;padding:9px 12px;border-radius:6px;
            font-size:0.82rem;font-weight:600;transition:background 0.15s;"
     onmouseover="this.style.background='#1d4ed8'"
     onmouseout="this.style.background='#1e40af'">
    <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24"
         fill="none" stroke="currentColor" stroke-width="2.2"
         stroke-linecap="round" stroke-linejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
      <polyline points="14 2 14 8 20 8"/>
      <line x1="12" y1="18" x2="12" y2="12"/>
      <polyline points="9 15 12 18 15 15"/>
    </svg>
    Samenvatting (PDF)
  </a>
</div>
```

Replace `<slug>` with the actual filename (e.g. `samenvatting_barbara_liskov.pdf`).

---

## Step 6 — Quality checklist before handing to the user

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
- [ ] (if --pdf) `samenvatting_*.pdf` exists in the project folder and is non-empty
- [ ] (if --pdf) Sidebar shows "Samenvatting (PDF)" download button
- [ ] (if --pdf) All chapter timecodes in the PDF match those in `index.html`
