# Wikidich Ebook Creator

A Python tool to download Vietnamese web novels from [truyenwikidich.net](https://truyenwikidich.net) and convert them into offline EPUB ebooks.

## Features

- **Modern PyQt6 GUI**: User-friendly graphical interface for local use
- **Automated Scraping**: Downloads complete novels with all chapters from truyenwikidich.net
- **EPUB Generation**: Creates properly formatted EPUB files with custom fonts
- **Volume Support**: Automatically detects and organizes chapters by volumes
- **Smart Updates**: Checks for new chapters and only downloads what's needed
- **Pagination Handling**: Automatically handles multi-page table of contents
- **Resume Support**: Continue from a specific chapter number
- **Auto ChromeDriver Management**: No manual ChromeDriver installation needed
- **Offline Reading**: Read your favorite novels offline on any EPUB reader

## Quick Start (Local Setup)

### For Local Use (Windows/macOS/Linux)

1. **Prerequisites**:
   - Python 3.7+
   - Google Chrome browser (ChromeDriver is auto-managed!)

2. **Clone and Setup**:
   ```bash
   git clone https://github.com/ngocanh54/wikidich_ebook.git
   cd wikidich_ebook

   # Optional but recommended: Create virtual environment
   python3 -m venv venv  # Use 'python' on Windows
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Run automated setup
   python3 setup_local.py  # Use 'python' on Windows
   ```

3. **Launch GUI**:
   ```bash
   python3 gui.py  # Use 'python' on Windows
   ```

That's it! The setup script will:
- ✓ Check your Python version
- ✓ Verify Google Chrome is installed
- ✓ Install all Python dependencies
- ✓ Automatically download and manage ChromeDriver (no manual setup needed!)

## Requirements

### For Local Use (Recommended)

**Minimal Requirements:**
- Python 3.7 or higher
- Google Chrome browser
- That's it! ChromeDriver is automatically managed by `webdriver-manager`

**Python Dependencies** (installed automatically by `setup_local.py`):
```bash
pip install -r requirements.txt
```

Key dependencies:
- PyQt6 (Modern GUI framework)
- selenium (Web automation)
- webdriver-manager (Automatic ChromeDriver management)
- beautifulsoup4 (HTML parsing)
- ebooklib (EPUB creation)
- And more (see requirements.txt)

### For Google Colab (Advanced Users)

If using Google Colab, you'll need to manually install Chrome and ChromeDriver:

```bash
apt -y update
apt install -y wget curl unzip

# Install Chrome
wget -O ./google-chrome-stable_current_amd64.deb https://mirror.cs.uchicago.edu/google-chrome/pool/main/g/google-chrome-stable/google-chrome-stable_142.0.7444.134-1_amd64.deb
dpkg -i google-chrome-stable_current_amd64.deb

# ChromeDriver is auto-managed by webdriver-manager, no manual install needed!
```

## Project Structure

The project is now organized into a modular package:

```
wikidich_ebook/
├── wikidich_ebook/           # Main package
│   ├── __init__.py           # Package initialization
│   ├── models.py             # Data classes (BookInfo, Chapter)
│   ├── config.py             # Configuration and constants
│   ├── utils.py              # Utility functions
│   ├── scraper.py            # Web scraping (auto ChromeDriver management)
│   ├── parser.py             # HTML parsing functions
│   ├── downloader.py         # Chapter downloading
│   ├── epub_builder.py       # EPUB creation
│   └── workflow.py           # Main workflow orchestration
├── gui.py                    # PyQt6 GUI application
├── main.py                   # CLI entry point
├── setup_local.py            # Local environment setup script
├── requirements.txt          # Python dependencies
├── .gitignore                # Git ignore file (excludes ebooks, downloads)
└── README.md                 # This file
```

### Module Description

- **models.py**: Defines `BookInfo` and `Chapter` data classes
- **config.py**: Contains all configuration constants (URLs, timeouts, delays)
- **utils.py**: Utility functions for file operations, URL parsing
- **scraper.py**: Web scraping with Selenium and BeautifulSoup
- **parser.py**: HTML parsing for metadata and table of contents
- **downloader.py**: Chapter downloading with retry logic
- **epub_builder.py**: EPUB file creation and formatting
- **workflow.py**: Main workflow orchestration functions

## Usage

### 1. GUI Interface (Recommended for Local Use)

Launch the modern PyQt6 interface:

```bash
python3 gui.py  # Use 'python' on Windows
```

**Features:**
- 🎨 Clean, modern interface
- 📊 Real-time progress tracking
- 📝 Live log output
- ⚙️ Easy configuration options
- 🔘 Multiple operation modes (Full, Check, TOC, Download, EPUB)
- 📁 Custom output folder selection

**How to use:**
1. Paste the novel's table of contents URL
2. Configure options (start chapter, volume structure, output folder)
3. Click "Download & Create EPUB" or choose specific operations
4. Monitor progress in the log output
5. Get notified when complete!

### 2. Command Line Interface

```bash
# Full workflow - download and create ebook
python3 main.py "https://truyenwikidich.net/truyen/your-novel-url"

# Start from a specific chapter
python3 main.py "https://truyenwikidich.net/truyen/your-novel-url" --start-chapter 100

# Force volume structure
python3 main.py "https://truyenwikidich.net/truyen/your-novel-url" --volume-structure yes

# Only check for updates
python3 main.py "https://truyenwikidich.net/truyen/your-novel-url" --check-only

# Only extract table of contents
python3 main.py "https://truyenwikidich.net/truyen/your-novel-url" --toc-only

# Only download chapters (requires TOC)
python3 main.py "https://truyenwikidich.net/truyen/your-novel-url" --download-only

# Only create EPUB (requires downloaded chapters)
python3 main.py "https://truyenwikidich.net/truyen/your-novel-url" --epub-only

# Manual pagination
python3 main.py "https://truyenwikidich.net/truyen/your-novel-url" --pages "1,2,3,4,5"
```

> **Note:** Use `python` instead of `python3` on Windows.

### Python API Usage

#### Basic Usage

```python
from wikidich_ebook import download_n_make_ebook_wikidich

# Download and create ebook from the beginning
download_n_make_ebook_wikidich(
    url_toc="https://truyenwikidich.net/truyen/your-novel-url",
    latest_chapter_read=0
)
```

#### Advanced Usage

##### Resume from a Specific Chapter

```python
from wikidich_ebook import download_n_make_ebook_wikidich

download_n_make_ebook_wikidich(
    url_toc="https://truyenwikidich.net/truyen/your-novel-url",
    latest_chapter_read=100  # Start from chapter 100
)
```

##### Control Volume Structure

```python
from wikidich_ebook import download_n_make_ebook_wikidich

download_n_make_ebook_wikidich(
    url_toc="https://truyenwikidich.net/truyen/your-novel-url",
    latest_chapter_read=0,
    use_volume_structure=True  # Force volume-based TOC
)
```

##### Manual Pagination Control

```python
from wikidich_ebook import check_if_updated, get_toc, download_truyen, make_ebook

url = "https://truyenwikidich.net/truyen/your-novel-url"
_, folder = check_if_updated(url)

# Manually specify pages to download
get_toc(
    url_toc=url,
    output_folder=folder,
    check_pagination=True,
    page_list=[1, 2, 3, 4, 5],
    is_manual=True
)

download_truyen(folder, latest_chapter_read=0)
make_ebook(folder, latest_chapter_read=0)
```

##### Using Individual Modules

```python
# Import specific functions from modules
from wikidich_ebook.scraper import get_url_content, setup_webdriver
from wikidich_ebook.parser import parse_book_metadata
from wikidich_ebook.models import BookInfo, Chapter

# Use individual components
soup = get_url_content("https://truyenwikidich.net/truyen/example")
book_info = parse_book_metadata(soup, "https://truyenwikidich.net/truyen/example")
print(f"Title: {book_info.title}")
print(f"Author: {book_info.author}")
```

## How It Works

1. **Check for Updates**: Fetches book metadata and checks if new chapters are available
2. **Download Cover**: Saves the book cover image locally
3. **Extract TOC**: Scrapes the table of contents, including volume information
4. **Download Chapters**: Downloads each chapter's HTML content with retry logic
5. **Create EPUB**: Compiles all chapters into a properly formatted EPUB file

## Output Structure

```
output-folder/
├── info.json                    # Book metadata
├── toc.csv                      # Table of contents
├── output-folder_bookcover.jpg  # Cover image
├── chap_0001.html              # Chapter files
├── chap_0002.html
├── ...
├── download_log.log            # Download log
└── BookTitle.epub              # Final EPUB file
```

## Data Classes

### BookInfo
Stores book metadata including title, author, status, URLs, and update information.

### Chapter
Represents a single chapter with chapter number, name, URL, and optional volume information.

## Key Functions

- `download_n_make_ebook_wikidich()`: Main workflow function
- `check_if_updated()`: Check for new chapters
- `get_toc()`: Extract table of contents
- `download_truyen()`: Download all chapters
- `make_ebook()`: Create EPUB file

## Configuration

### Constants

- `CHAPTERS_PER_PAGE`: 501 (default pagination size)
- `USER_AGENT`: Chrome user agent string
- Font: Playwrite IT Moderna (auto-downloaded)

### Custom Delays

The script includes random delays (2-7 seconds) between chapter downloads to avoid rate limiting.

## Google Colab Support

The script includes Google Drive integration for Colab environments:

```python
from google.colab import drive
drive.mount("/content/drive", force_remount=True)
```

EPUB files are automatically saved to `/content/drive/MyDrive/TongHopTruyenEpub/` if the path exists.

## Features in Detail

### Volume Detection
- Automatically detects if a novel has multiple volumes
- Creates nested TOC structure in EPUB when volumes are detected
- Displays volume distribution statistics

### Smart Resume
- Tracks the latest chapter downloaded
- Skips already downloaded chapters
- Retry logic for failed downloads

### Multi-page TOC Support
- Auto-detects pagination
- Can manually specify page ranges
- Handles complex volume structures

## Example

```python
# Download a complete novel
from wikidich_ebook import download_n_make_ebook_wikidich

download_n_make_ebook_wikidich(
    url_toc="https://truyenwikidich.net/truyen/di-the-gioi-cua-hang-pho-kinh-doanh-chi--ZB2Do1S4CBIeL0Br",
    latest_chapter_read=0,
    use_volume_structure=False
)
```

## Git Tracking

The `.gitignore` file is configured to exclude all generated files from version control:

- EPUB, MOBI, PDF files (all ebook formats)
- Downloaded HTML chapter files
- Book cover images
- Metadata files (info.json, toc.csv)
- Downloaded fonts
- Book output folders
- Python cache and virtual environments
- Log files

This ensures your repository stays clean and only tracks source code, not generated content. You can safely run the tool locally without worrying about accidentally committing large ebook files.

## Building macOS App (DMG Distribution)

Want to create a standalone macOS .app that can be distributed as a DMG? Follow these steps:

### Prerequisites
- macOS 10.13+ (High Sierra or later)
- Python 3.7+
- Xcode Command Line Tools

### Build Steps

1. **Install build dependencies**:
   ```bash
   pip install -r requirements-build.txt
   ```

2. **Run the build script** (requires sudo for cleaning previous builds):
   ```bash
   sudo ./build_mac_app.sh
   ```

   Note: `sudo` is required to clean previous build artifacts. You'll be prompted for your password.

3. **Find your DMG**:
   ```bash
   # The DMG will be in the dist/ folder
   ls dist/*.dmg
   ```

### What Gets Built

- **`.app` bundle**: `dist/Wikidich Ebook Creator.app`
  - Standalone macOS application
  - Includes all dependencies
  - No Python installation required for end users

- **`.dmg` installer**: `dist/WikidichEbookCreator-{version}.dmg`
  - Drag-and-drop installer
  - Compressed disk image (~70-80MB)
  - Ready for distribution

### Distribution

Users can install by:
1. Downloading the DMG file
2. Opening it
3. Dragging "Wikidich Ebook Creator" to Applications folder
4. Launching from Applications

### Auto-Update

The app automatically:
- Checks for updates on GitHub releases on startup
- Notifies users when new versions are available
- Opens download page with one click
- Users just download new DMG and replace the app

### Creating a GitHub Release

To enable auto-updates for users:

1. Create a new release on GitHub
2. Tag it with version (e.g., `v2.0.0`)
3. Upload the DMG file as a release asset
4. Users' apps will detect and prompt to download

## Troubleshooting

### ChromeDriver Issues
Ensure ChromeDriver version matches your Chrome version. Update the download URL in the installation script if needed.

### Rate Limiting
If you encounter rate limiting, the script includes automatic delays. You can increase the delay range in `download_chapters()`.

### Font Download Errors
The script downloads fonts from globalfonts.pro. If this fails, manually download and place the font file in the working directory.

## License

This project is provided as-is for personal use. Respect copyright laws and terms of service of the source website.

## Disclaimer

This tool is for personal backup and offline reading purposes only. Please support the original authors and translators by visiting the official website.
