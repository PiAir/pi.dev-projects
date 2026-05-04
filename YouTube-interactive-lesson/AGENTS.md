# AGENTS.md

This file provides guidance to OpenCode when working with this YouTube Interactive Lesson Builder.

## Project Overview

This package provides tools for building **interactive educational video experiences** on top of YouTube videos. It contains:

- **`.agents/skills/youtube-interactive-lesson/`** — A skill for building a complete interactive lesson page from a YouTube URL (subtitles, chapters, quiz).
- **`examples/Barbara-Liskov/`** — A working example demonstrating the complete interactive video pattern with PDF generation.

No build pipeline, package manager, or test framework is required — the output is a self-contained HTML file loadable directly in a browser.

## Skills

### `youtube-interactive-lesson` skill

Invoked via `/youtube-interactive-lesson`. Given a YouTube URL, builds a complete interactive lesson page with synced subtitles, chapter navigation, and quiz. Full instructions — including hard-won lessons about Vue 3 gotchas, video sizing, and subtitle parsing — are in `.agents/skills/youtube-interactive-lesson/SKILL.md`.

Post-processes the downloaded `.vtt` file with Python to strip HTML tags, resolve XML entities, and deduplicate repeated lines. Translates subtitles by spawning subagents (max 5 in parallel, 50 lines each) — never via an external Python script.

**Dependency:** `yt-dlp` — the skill auto-installs it if missing using pip.

## Example

### `examples/Barbara-Liskov/`

A complete interactive lesson built from a 35-minute interview with Barbara Liskov (Turing Award winner). This example demonstrates all features including PDF generation. To view it locally:

```bash
cd examples/Barbara-Liskov
python -m http.server 8770
# Open http://localhost:8770
```

Architecture:

- `index.html` — Vue 3 + Tailwind CSS from CDN. Sidebar + video + subtitle bar + tabbed content + quiz, all in one file.
- `subtitles_{en,nl}.vtt` — Clean WebVTT files (849 cues each) generated from raw YouTube auto-captions.
- `samenvatting_barbara_liskov.pdf` — Dutch PDF summary with detailed chapter explanations.

## Patterns Used Across Examples

- **YouTube iframe API** — All players use `onYouTubeIframeAPIReady` and `seekTo()` for timestamped navigation.
- **VTT subtitles** — Parsed client-side; displayed in a dedicated `<div>` bar *below* the iframe (not overlaid on it) synced via `requestAnimationFrame`.
- **Timestamp links** — UI elements call `player.seekTo(seconds, true)` to jump to relevant moments.
- **Local HTTP server required** — YouTube iframe API refuses to load from `file://`. Always serve with `python -m http.server 8765` from the project folder.

## Hard-won Technical Lessons

These mistakes have already been made and fixed. Do not repeat them.

### Vue 3 in-DOM templates lowercase camelCase identifiers

When Vue 3 is used via CDN in a plain HTML file (not a `.vue` SFC), the browser parses the HTML before Vue compiles it. The HTML parser lowercases all attribute names, and Vue normalises identifiers accordingly. **Any camelCase name returned from `setup()` becomes inaccessible under its camelCase spelling after the first reactive update.**

The failure mode is silent and delayed: the component renders correctly on first load, but after a reactive update (e.g. a click) Vue tries to re-render using lowercased names, finds them undefined, silently aborts the update, and the DOM freezes.

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

Also rename `v-for` loop variables to avoid shadowing: use `v-for="t in tabs"` not `v-for="tab in tabs"`.

### `>` inside `{{ }}` expressions corrupts the template

The browser HTML parser sees `>` in a mustache expression as closing an HTML tag, mangling everything after it into attribute names. Symptoms: button text like `volgende →="" <="" button="">`.

```html
<!-- WRONG: -->
{{ qidx < questions.length-1 ? 'Volgende →' : 'Resultaten' }}

<!-- CORRECT: -->
<span v-if="qidx < questions.length-1">Volgende &rarr;</span>
<span v-else>Resultaten</span>
```

### Video sizing: `height` + `aspect-ratio`, not `max-height` + `aspect-ratio`

`max-height` + `aspect-ratio` on the same element conflict: the browser clips the height without adjusting the width, producing a stretched or incorrectly-proportioned video.

```css
/* CORRECT — height is primary, aspect-ratio derives width: */
#player-wrapper {
  position: relative;
  height: 42vh;
  aspect-ratio: 16 / 9;
  max-width: 100%;
}
#player-wrapper iframe,
#player-wrapper > div {
  position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0;
}
```

Also pass `width: '100%', height: '100%'` to `new YT.Player(...)` or the API defaults to 640×390.

### Subtitle bar: below the iframe, not overlaid on it

CSS overlays on YouTube iframes are unreliable (iframe stacking context, pointer-event blocking). Place the subtitle bar as a sibling element directly below `#player-wrapper`, not as a child positioned over it.

### CRLF line endings break VTT parsing

VTT files downloaded from YouTube may have CRLF (`\r\n`) or LF (`\n`) line endings depending on platform. The blank-line separator between cues must be normalized. `text.split(/\n\n+/)` on a CRLF file treats the entire file as one block, joining all 500+ cues into a single string — all subtitles appear simultaneously.

**Always normalise before parsing**, both in Python and in browser JavaScript:

```python
content = content.replace('\r\n', '\n').replace('\r', '\n')
```

```javascript
const normalised = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
```

### YouTube rolling-caption VTT format

YouTube auto-captions are not always one-sentence-per-cue. In some cases each cue block contains the *previous* sentence plus one new word, with inline `<HH:MM:SS.mmm><c>word</c>` timing tags. To get clean display cues: strip all tags, take only the **last text line** of each block, skip cues shorter than 0.05 s, and deduplicate consecutive identical lines by extending the previous cue's end time.

### Never use an external script or hardcoded dict to translate subtitles

A video has 400–800 subtitle cues. Two approaches that do not work:

- **Hardcoding a Python dict** — the model stops partway and leaves the rest untranslated, silently.
- **A Python script that loops over cues making API calls** — times out before finishing for any video longer than ~15 minutes, silently, with no error and missing subtitles.

**Always translate using subagents.** Split the unique lines into chunks of 50 and spawn subagents that translate directly. Process at most **5 subagents in parallel** to avoid overloading the local LLM server, then wait for that group before starting the next. Merge all returned JSON dicts at the end. Full pattern is in the `youtube-interactive-lesson` skill, Step 3.

### Never request `nl-en` (auto-translated) subtitles from YouTube

YouTube returns HTTP 429 for auto-translated tracks (`nl-en`, `de-en`, etc.) without browser cookies. Manual tracks (`en`, `nl`) download fine. Only request `en`, `en-en`, or `nl` — never a `LANG-en` auto-translated variant.

### Strip `>>` speaker markers from subtitles

YouTube uses `>>` to mark speaker changes. These appear literally in display text if not removed:

```javascript
const clean = txt.replace(/^>>\s*/g, '').replace(/\s*>>\s*/g, ' ').trim();
```

### Quiz answer option length must be uniform

Students recognise that the correct answer is usually the longest option, because it needs to be precise enough to be unambiguously right. Write all four options at similar length — extend wrong answers with plausible-but-incorrect detail rather than writing short decoys.
