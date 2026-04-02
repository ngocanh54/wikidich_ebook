# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Wikidich Ebook Creator downloads Vietnamese web novels from truyenwikidich.net and wikicv.net and converts them to EPUB format. The tool is designed for **personal offline reading only** and includes respectful scraping practices (2-7 second delays between chapter downloads).

**Supported Domains:**
- `truyenwikidich.net` (original)
- `wikicv.net` (new domain with same structure)

**Version:** 2.2.0

## Development Commands

### Setup
```bash
# Create venv and install dependencies
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
playwright install chromium   # downloads Playwright's bundled Chromium (no system Chrome needed)

# Or use the guided setup script
python3 setup_local.py
```

### Running the Application
```bash
# Launch GUI
python3 gui.py

# CLI - Download complete novel
python3 main.py "https://wikicv.net/truyen/novel-url"
# Or: python3 main.py "https://truyenwikidich.net/truyen/novel-url"

# CLI - Resume from chapter 100
python3 main.py "URL" --start-chapter 100

# CLI - Check for updates only
python3 main.py "URL" --check-only

# CLI - Extract TOC only
python3 main.py "URL" --toc-only

# CLI - Download chapters only (no EPUB creation)
python3 main.py "URL" --download-only

# CLI - Create EPUB from already downloaded chapters
python3 main.py "URL" --epub-only

# CLI - Force volume/flat structure in EPUB TOC
python3 main.py "URL" --volume-structure yes   # or: no, auto (default)

# CLI - Manual pagination (for novels with known page count)
python3 main.py "URL" --pages "1,2,3,4,5"
```

### Building macOS App
```bash
# Install build dependencies (already included if using .venv)
uv pip install -r requirements-build.txt

# Build DMG installer
./build_mac_app.sh

# Output: dist/WikidichEbookCreator-{version}.dmg
```

## Architecture

### Core Pipeline Flow
The application follows a modular pipeline architecture:

1. **Metadata Extraction** (`check_if_updated()`)
   - Scrapes book metadata (title, author, cover, latest chapter)
   - Checks if content has been updated since last run
   - Creates output folder structure

2. **Table of Contents** (`get_toc()`)
   - Extracts all chapter links from TOC page(s)
   - Handles pagination (501 chapters per page by default)
   - Saves to `toc.csv` with chapter numbers, names, URLs, and volume info

3. **Chapter Download** (`download_truyen()`)
   - Downloads individual chapters using Selenium
   - Implements respectful delays (2-7 seconds between requests)
   - Saves chapters as HTML files (`chap_0001.html`, etc.)
   - Logs progress to `download_log.log`
   - Automatically retries failed downloads

4. **EPUB Creation** (`make_ebook()`)
   - Downloads custom font (Playwrite IT Moderna)
   - Builds EPUB file with proper structure
   - Optionally organizes by volumes
   - Adds metadata, cover image, and styling

### Module Responsibilities

The `wikidich_ebook/` directory is a Python package. `__init__.py` re-exports the full public API.

- **workflow.py**: Orchestrates the entire process; entry point for both CLI and GUI
- **models.py**: Data classes (`BookInfo`, `Chapter`)
- **scraper.py**: `requests`-based fetching + Selenium WebDriver setup and chapter content extraction
- **parser.py**: BeautifulSoup HTML parsing for book metadata and TOC chapter extraction
- **downloader.py**: Chapter downloading loop, retry logic, volume detection
- **epub_builder.py**: EPUB file creation with ebooklib
- **utils.py**: Shared utilities (URL parsing, image downloading, safe filename creation)
- **config.py**: Constants (USER_AGENT, delays, font settings, etc.)
- **updater.py**: Update checking for GUI app
- **main.py**: CLI interface with argparse (top-level, outside package)
- **gui.py**: PyQt6 GUI application (top-level, outside package)

### Key Technical Details

**Web Scraping:**
- Two-tier scraping: `get_url_content()` uses `requests` (lightweight, for metadata and chapter content); TOC navigation uses Playwright (requires JavaScript execution to handle pagination clicks)
- Playwright uses its own bundled Chromium — no system Chrome or ChromeDriver needed
- Respectful delays: `MIN_DELAY=2`, `MAX_DELAY=7` seconds
- User-Agent spoofing to mimic Chrome browser

**Data Storage:**
- Each novel gets its own folder in current directory or Google Drive (Colab)
- Folder structure:
  ```
  novel-name/
  ├── info.json              # Book metadata
  ├── toc.csv                # Chapter list
  ├── novel-name_bookcover.jpg
  ├── chap_0001.html         # Individual chapters
  ├── download_log.log       # Download history
  └── NovelName.epub         # Final output
  ```

**EPUB Generation:**
- Custom font embedded: Playwrite IT Moderna
- Volume structure detection (looks for "Quyển" or "Tập" keywords)
- CSS styling included for proper Vietnamese text rendering
- Metadata preserved (title, author, language=vi)

## Important Constraints

### Rate Limiting
Always maintain the delay between chapter downloads (configured in `config.py`). Do not reduce `MIN_DELAY` or `MAX_DELAY` as this helps:
- Prevent server overload
- Avoid IP blocking
- Respect the source website

### Playwright Browser
Playwright manages its own Chromium bundle — no system Chrome required. After installing dependencies, run `playwright install chromium` once to download the browser. If upgrading the `playwright` package, re-run this command as browser binaries are versioned alongside the package.

### Volume Structure Detection
The code in `downloader.py:check_multiple_volumes()` looks for Vietnamese volume keywords:
- "Quyển" (volume)
- "Tập" (volume/book)

When adding volume detection logic, ensure these keywords remain recognized.

## Testing Notes

There are no automated tests in this repository. When making changes:
- Test the full pipeline: download → EPUB creation
- Verify with a small novel first (under 50 chapters)
- Check EPUB validity using Calibre or similar tools
- Test GUI thoroughly if modifying GUI code
- Verify macOS app build works before releasing

## Common Pitfalls

1. **Selenium WebDriver Issues**: Always use `webdriver-manager` to handle ChromeDriver versions. Don't hardcode driver paths.

2. **Encoding Problems**: All file operations should use `encoding='utf-8'` for Vietnamese text support.

3. **Chapter Numbering**: Chapters are zero-padded (e.g., `chap_0001.html`) to ensure correct sorting. Maintain this format when modifying download logic.

4. **Volume Structure**: The `use_volume_structure` parameter in `make_ebook()` can be `True`, `False`, or `None` (auto-detect). Respect user choice when explicitly set.

5. **macOS App Building**: The build script auto-detects `.venv` and uses it for Python and PyInstaller. No `sudo` needed — run as a normal user.
