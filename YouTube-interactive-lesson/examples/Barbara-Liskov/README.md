# Barbara Liskov – Turing Award Lecture Example

This directory contains a **complete, working interactive lesson** built using the `youtube-interactive-lesson` skill.

**Source video:**  
*ACM Turing Award Lecture "The Power of Abstraction" by Barbara Liskov*  
https://www.youtube.com/watch?v=qAKrMdUycb8  
(35 minutes, 2013)

## What's Included

- **`index.html`** — UI template (Vue 3 + Tailwind CSS from CDN), loads `lesson-data.json` at runtime
- **`lesson-data.json`** — chapters, quiz questions, video metadata, subtitle language list
- **`subtitles_en.vtt`** — Clean English subtitles (849 cues)
- **`subtitles_nl.vtt`** — Dutch translation (849 cues, identical timestamps)
- **`samenvatting_barbara_liskov.pdf`** — Dutch PDF summary with chapter breakdowns (20 KB)

## Features Demonstrated

- **8 chapters** with timestamped navigation
- **Multi-language subtitle toggle** (EN/NL/Uit) — dynamically built from `subtitleLangs`
- **Synced subtitle bar** below the video (not overlaid)
- **Tabbed content per chapter** (description + key points + subtopics)
- **8-question quiz** with shuffled options, feedback, and video clip links
- **PDF download button** in sidebar
- **Data/UI split** — regenerate quiz/chapters without touching the HTML template

## How to View Locally

The YouTube iframe API requires an HTTP origin (not `file://`). Start a local web server from this directory:

```bash
# Python 3
python -m http.server 8770

# Python 2 (if python points to version 2)
python3 -m http.server 8770
```

Then open **http://localhost:8770/** in your browser.

Press `Ctrl+C` in the terminal to stop the server.

## How to Run Tests

Open **`tests/test-vtt-parser.js`** in any browser (no server needed). It runs 5 test suites:
1. VTT parser correctness
2. Subtitle sync accuracy
3. Quiz shuffle statistics
4. Multi-language support structure
5. lesson-data.json validation

## What's NOT Included

The following intermediate files were used during generation but are **not needed to view the example**:

- `transcript.en.vtt` — Raw YouTube auto-captions (287 KB, rolling format)
- `gen_nl_vtt.py` — Python script that parsed and translated subtitles
- `gen_pdf.py` — Python script that generated the PDF summary
- `translations.json`, `unique_lines.json` — Translation build artifacts

These files are video-specific and not useful as templates. The `.pi/skills/youtube-interactive-lesson/SKILL.md` documents the generation patterns in detail.

## Technical Notes

- Built with Vue 3 and Tailwind CSS via CDN (no build pipeline)
- All reactive state uses lowercase variable names (Vue 3 in-DOM template requirement)
- Subtitle bar positioned below video iframe (not overlaid)
- Video sizing: `height: 42vh` + `aspect-ratio: 16/9` (no `max-height`)
- VTT line endings normalized for cross-platform compatibility
- Data/UI split: `lesson-data.json` contains all chapters, quiz, and metadata; `index.html` loads it via `fetch()`
- Multi-language toggle dynamically reads `subtitleLangs` from `lesson-data.json`
- Two-pass quiz generation for higher quality

## License

This example is provided under the MIT License (see `../../LICENSE`).
