# YouTube Interactive Lesson Builder

Transform any YouTube video into an interactive educational experience with synced subtitles, chapter navigation, quiz, and optional PDF summary.

## Features

- **Multi-language subtitles** — Any language pair, toggleable, synced to video playback
- **Chapter navigation** — Sidebar with clickable timestamps for quick navigation
- **Interactive quiz** — Two-pass generation (concept extraction + question) with shuffled options and clip links
- **PDF summary** — Optional detailed Dutch summary document with chapter explanations
- **Zero build step** — Pure HTML/CSS/JS using Vue 3 + Tailwind CSS from CDN
- **Data/UI split** — `lesson-data.json` (data) + `index.html` (template) for easy regeneration
- **Self-contained output** — HTML template loads all data via `fetch()` at runtime

## Quick Start

```bash
pi "Build an interactive lesson from https://www.youtube.com/watch?v=YOUR_VIDEO_ID -- pdf"
```

**Skill parameters:**
- `map: <folder>` — subfolder name (default: derived from video title)
- `webserver poort: <port>` — local HTTP server port (default: 8765)
- `--pdf` — also generate a Dutch PDF summary
- `--langs <list>` — subtitle languages (default: en,nl; e.g. `en,de,ja`)
- `--chunk-size <n>` — translation chunk size for adaptive tuning
- `--quizzes <n>` — number of quiz questions (default: 8)

**Example:**
```bash
pi "Build a lesson from https://www.youtube.com/watch?v=XYZ -- map: My-Lesson -- langs en,de -- pdf"
```

## What's Included

### Documentation
- **`.pi/skills/youtube-interactive-lesson/SKILL.md`** — Complete step-by-step implementation guide (pi package)
- **`AGENTS.md`** — Project patterns, architecture decisions, and critical gotchas
- **`package.json`** — pi package manifest (skills, extensions, prompts)

### Template
- **`extensions/lesson-template.html`** — Reusable HTML template (loads `lesson-data.json`)

### Example
- **`examples/Barbara-Liskov/`** — Working example from a 35-minute interview
  - View locally: `cd examples/Barbara-Liskov && python -m http.server 8770`
  - Open: `http://localhost:8770`

### Tests
- **`tests/test-vtt-parser.js`** — Standalone test suite (VTT parsing, subtitle sync, quiz shuffle, data validation)

## Output Structure

When you build a lesson, the skill creates:

```
My-Lesson/
├── index.html              # HTML template (loaded from extensions/)
├── lesson-data.json        # Chapters, quiz, video metadata
├── subtitles_en.vtt        # Base subtitles
├── subtitles_en-de.vtt     # Target language 1
├── subtitles_en-nl.vtt     # Target language 2
├── samenvatting_*.pdf      # PDF summary (if --pdf)
├── transcript.en.vtt       # Raw YouTube download (intermediate)
├── gen_nl_vtt.py           # VTT parser script (intermediate)
└── translations.json       # Translation cache (intermediate)
```

Only `index.html`, `lesson-data.json`, the `.vtt` files, and optional `.pdf` are needed to view the lesson.

## Requirements

### System
- **Python 3.x** (Python 3.7+ recommended)
- **pi** — interactive coding agent
- Platform: Windows, Linux, macOS, or WSL2

### Python Packages
Auto-installed by the skill when needed:
- `yt-dlp` — YouTube subtitle download
- `reportlab` — PDF generation (only if `--pdf` flag used)

### LLM Requirements
The skill uses subagents for subtitle translation:
- Subagents run sequentially (one at a time) to avoid overloading slower local models
- Chunk size auto-tunes based on measured model speed
- Typical video (20-30 min) requires ~10-40 chunks depending on chunk size
- Each chunk is saved to `translations.json` immediately — restarts only redo untranslated chunks
- Total translation time: 15-40 minutes depending on model speed; this is expected, do not interrupt

## Technical Overview

### Architecture
- **Frontend**: Vue 3 (CDN) + Tailwind CSS (CDN), no build step required
- **Data layer**: `lesson-data.json` — chapters, quiz, video metadata, subtitle languages
- **UI layer**: `index.html` — loads data via `fetch(DATA_URL)` at mount time
- **Video player**: YouTube iframe API with `seekTo()` for timestamp navigation
- **Subtitles**: WebVTT format, parsed client-side, synced via `requestAnimationFrame`

### Data/UI Split

All chapter and quiz data is extracted to `lesson-data.json`. The HTML template (`extensions/lesson-template.html`) loads it via:

```javascript
const DATA_URL = 'lesson-data.json';
const data = ref(null);
onMounted(async () => { data.value = await (await fetch(DATA_URL)).json(); });
```

Benefits:
- Quiz/chapters can be regenerated without touching the UI
- The HTML template is reusable across videos
- Data files are diff-friendly; the template stays stable

### Key Design Decisions
- **No overlay subtitles** — Subtitle bar placed below video iframe to avoid z-index issues
- **Lowercase Vue state** — All reactive refs use lowercase names to avoid Vue 3 in-DOM template gotcha
- **Adaptive translation** — Chunk size auto-tunes based on measured model speed
- **Two-pass quiz** — Concept extraction then question generation, with quality checks
- **Multi-language** — Any language pair via `--langs` parameter
- **Disk-based checkpointing** — Already-translated lines never need retranslation
- **CRLF normalization** — Always normalize line endings before parsing VTT files

See `AGENTS.md` for detailed explanations of these decisions.

## Platform Notes

### Windows
- Use PowerShell or Command Prompt
- `python -m http.server` works out of the box
- Write Python commands to `.py` scripts — do not use long one-liners in PowerShell

### Linux / macOS / WSL2
- Use any terminal
- May need `python3` instead of `python` on some systems
- Server runs in foreground; press `Ctrl+C` to stop

## Example Output

The Barbara Liskov example demonstrates:
- **Video**: 35-minute interview with Turing Award winner Barbara Liskov
- **Chapters**: 8 chapters with 2-4 sub-topics each
- **Subtitles**: 849 cues in both Dutch and English
- **Quiz**: 8 questions (two-pass generation) with shuffled options and clip links
- **PDF**: 20 KB summary with detailed chapter explanations
- **Data/UI split**: `lesson-data.json` + reusable `index.html` template
- **Multi-language toggle**: dynamically built from `subtitleLangs`

Total size: ~170 KB for complete working example

## Important Notes

- **HTTP server required** — YouTube iframe API refuses `file://` origins; always serve via HTTP
- **Translation quality** — Depends on your local model; 35B+ parameter models recommended
- **Processing time** — Expect 10-15 minutes total for a 20-minute video (download + translation + generation)
- **Manual review recommended** — Generated chapters and quiz questions should be reviewed for accuracy

## Running Tests

Open `tests/test-vtt-parser.js` in any browser. The standalone test suite covers:
1. VTT parser correctness (rolling captions, CRLF, dedup, speaker markers, entity decoding)
2. Subtitle sync accuracy (mock `getCurrentTime()` against known boundaries)
3. Quiz shuffle statistics (100+ runs verify even distribution)
4. lesson-data.json structure validation

## Documentation

- **Implementation guide**: `.pi/skills/youtube-interactive-lesson/SKILL.md`
- **Patterns & gotchas**: `AGENTS.md`
- **Example explanation**: `examples/Barbara-Liskov/README.md`
- **HTML template**: `extensions/lesson-template.html`

## License

This project is released under the MIT License. See `LICENSE` for details.

## Acknowledgments

Built with pi, an AI-powered coding agent platform.
