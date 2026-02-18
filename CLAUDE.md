# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Wikidich Ebook Creator downloads Vietnamese web novels from truyenwikidich.net and converts them to EPUB format. The tool is designed for **personal offline reading only** and includes respectful scraping practices (2-7 second delays between chapter downloads).

**Version:** 2.1.0

## Development Commands

### Setup
```bash
# Initial setup (installs dependencies and configures ChromeDriver)
python3 setup_local.py

# Install dependencies manually
pip install -r requirements.txt
```

### Running the Application
```bash
# Launch GUI
python3 gui.py

# CLI - Download complete novel
python3 main.py "https://truyenwikidich.net/truyen/novel-url"

# CLI - Resume from chapter 100
python3 main.py "URL" --start-chapter 100

# CLI - Check for updates only
python3 main.py "URL" --check-only

# CLI - Download chapters only (no EPUB creation)
python3 main.py "URL" --download-only

# CLI - Create EPUB from already downloaded chapters
python3 main.py "URL" --epub-only
```

### Building macOS App
```bash
# Install build dependencies
pip install -r requirements-build.txt

# Build DMG installer (requires sudo for cleanup)
sudo ./build_mac_app.sh

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

- **workflow.py**: Orchestrates the entire process, provides high-level functions
- **models.py**: Data classes (`BookInfo`, `Chapter`)
- **scraper.py**: Selenium-based web scraping, ChromeDriver management
- **parser.py**: BeautifulSoup HTML parsing, metadata extraction
- **downloader.py**: Chapter downloading logic, volume detection
- **epub_builder.py**: EPUB file creation with ebooklib
- **utils.py**: Shared utilities (URL parsing, image downloading, etc.)
- **config.py**: Constants (USER_AGENT, delays, font settings, etc.)
- **updater.py**: Update checking for GUI app
- **main.py**: CLI interface with argparse
- **gui.py**: PyQt6 GUI application

### Key Technical Details

**Web Scraping:**
- Uses Selenium with Chrome in headless mode
- ChromeDriver auto-managed via webdriver-manager
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

### ChromeDriver Compatibility
The application requires Google Chrome to be installed. For Chrome 115+, webdriver-manager handles driver downloads automatically. If changing Selenium version, test with both older and newer Chrome versions.

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

5. **macOS App Building**: The build script requires `sudo` because it cleans old builds. This is intentional - don't remove the sudo requirement without understanding the cleanup process.
