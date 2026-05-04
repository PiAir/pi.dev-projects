# YouTube Interactive Lesson Builder

Transform any YouTube video into an interactive educational experience with synced subtitles, chapter navigation, quiz, and optional PDF summary.

## Features

- **Dual-language subtitles** — Dutch + English, toggleable, synced to video playback
- **Chapter navigation** — Sidebar with clickable timestamps for quick navigation
- **Interactive quiz** — Multiple-choice questions with video clip links to relevant moments
- **PDF summary** — Optional detailed Dutch summary document with chapter explanations
- **Zero build step** — Pure HTML/CSS/JS using Vue 3 + Tailwind CSS from CDN
- **Self-contained output** — Single `index.html` with embedded data, plus subtitle files

## Quick Start

```bash
opencode run "/youtube-interactive-lesson https://www.youtube.com/watch?v=YOUR_VIDEO_ID -- map: My-Lesson, --pdf" \
  --model <your-local-llm>
```

**Parameters:**
- `map: <folder>` — subfolder name (default: derived from video title)
- `webserver poort: <port>` — local HTTP server port (default: 8765)
- `--pdf` — also generate a Dutch PDF summary

**Example:**
```bash
opencode run "/youtube-interactive-lesson https://www.youtube.com/watch?v=dQw4w9WgXcQ -- map: Rick-Astley, webserver poort: 8888, --pdf"
```

## What's Included

### Documentation
- **`.agents/skills/youtube-interactive-lesson/SKILL.md`** — Complete step-by-step implementation guide
- **`AGENTS.md`** — Project patterns, architecture decisions, and critical gotchas learned through development

### Example
- **`examples/Barbara-Liskov/`** — Working example from a 35-minute interview
  - View locally: `cd examples/Barbara-Liskov && python -m http.server 8770`
  - Open: `http://localhost:8770`

## Output Structure

When you run the skill, it creates:

```
My-Lesson/
├── index.html              # Main interactive lesson page (all-in-one)
├── subtitles_en.vtt        # Clean English subtitles
├── subtitles_nl.vtt        # Dutch translation
├── samenvatting_*.pdf      # PDF summary (if --pdf flag used)
├── gen_nl_vtt.py           # VTT parser script (intermediate)
└── transcript.en.vtt       # Raw YouTube download (intermediate)
```

Only `index.html`, the `.vtt` files, and optional `.pdf` are needed to view the lesson.

## Requirements

### System
- **Python 3.x** (Python 3.7+ recommended)
- **OpenCode CLI** with local LLM support
- Platform: Windows, Linux, macOS, or WSL2

### Python Packages
Auto-installed by the skill when needed:
- `yt-dlp` — YouTube subtitle download
- `reportlab` — PDF generation (only if `--pdf` flag used)

### LLM Requirements
The skill uses subagents for subtitle translation:
- Must support 5 parallel subagent requests
- Typical video (20-30 min) requires ~15-20 translation groups
- Each group processes 50 subtitle lines
- Total translation time: 5-10 minutes depending on LLM speed

## Technical Overview

### Architecture
- **Frontend**: Vue 3 (CDN) + Tailwind CSS (CDN), no build step required
- **Video player**: YouTube iframe API with `seekTo()` for timestamp navigation
- **Subtitles**: WebVTT format, parsed client-side, synced via `requestAnimationFrame`
- **Data**: All chapters, quiz questions, and timestamps embedded in `index.html`

### Key Design Decisions
- **No overlay subtitles** — Subtitle bar placed below video iframe to avoid z-index issues
- **Lowercase Vue state** — All reactive refs use lowercase names to avoid Vue 3 in-DOM template gotcha
- **Subagent translation** — Never use hardcoded dicts or external API loops (both fail silently)
- **CRLF normalization** — Always normalize line endings before parsing VTT files

See `AGENTS.md` for detailed explanations of these decisions.

## Platform Notes

### Windows
- Use PowerShell or Command Prompt
- `python -m http.server` works out of the box

### Linux / macOS / WSL2
- Use any terminal
- May need `python3` instead of `python` on some systems
- Server runs in foreground; press `Ctrl+C` to stop

## Example Output

The Barbara Liskov example demonstrates:
- **Video**: 35-minute interview with Turing Award winner Barbara Liskov
- **Chapters**: 8 chapters with 2-4 sub-topics each
- **Subtitles**: 849 cues in both Dutch and English
- **Quiz**: 8 questions with shuffled options and clip links
- **PDF**: 20 KB summary with detailed chapter explanations

Total size: ~170 KB for complete working example

## Important Notes

- **HTTP server required** — YouTube iframe API refuses `file://` origins; always serve via HTTP
- **Translation quality** — Depends on your local LLM; 35B+ parameter models recommended
- **Processing time** — Expect 10-15 minutes total for a 20-minute video (download + translation + generation)
- **Manual review recommended** — Generated chapters and quiz questions should be reviewed for accuracy

## Documentation

- **Implementation guide**: `.agents/skills/youtube-interactive-lesson/SKILL.md`
- **Patterns & gotchas**: `AGENTS.md`
- **Example explanation**: `examples/Barbara-Liskov/README.md`

## License

This project is released under the MIT License. See `LICENSE` for details.

## Acknowledgments

Built with OpenCode, an AI-powered coding agent platform.
