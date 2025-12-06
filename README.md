# Wikidich Ebook Creator

Download Vietnamese web novels from [truyenwikidich.net](https://truyenwikidich.net) and read them offline on your phone, tablet, or e-reader!

---

## 📱 For Regular Users (Easiest Way)

### macOS Users - Just Download and Use!

**No coding needed!** Simply download the app and start creating ebooks.

1. **Download the App**
   - Go to [Releases](https://github.com/ngocanh54/wikidich_ebook/releases/latest)
   - Download `WikidichEbookCreator-2.1.0.dmg`

2. **Install**
   - Open the downloaded DMG file
   - Drag "Wikidich Ebook Creator" to your Applications folder
   - Done!

3. **First Time Launch**
   - Right-click the app → Click "Open" (first time only)
   - Your Mac will ask "Are you sure?" → Click "Open"
   - After first time, just double-click to open normally

4. **How to Use**
   - Open the app
   - Copy the novel's URL from truyenwikidich.net
   - Paste it into the app
   - Click "Download & Create EPUB"
   - Wait for it to finish
   - Find your EPUB file in the folder you chose!

**That's it!** 🎉 You can now read the EPUB on any device with an ebook reader app.

### What You Can Do

- ✅ Download entire novels automatically
- ✅ Resume from a specific chapter
- ✅ Watch progress in real-time
- ✅ Get organized EPUB files ready for reading
- ✅ Read offline on any device (phone, tablet, Kindle, etc.)

### App Features

- 📊 **Real-time Progress Bar** - See exactly how many chapters are downloaded
- 📝 **Live Logs** - Watch what's happening step-by-step
- ⚙️ **Easy Options** - Choose where to start, how to organize chapters
- 🔄 **Auto-Updates** - Get notified when a new version is available

---

## 💻 For Developers & Advanced Users

Want to run from source code, customize the tool, or use it on Windows/Linux? See the sections below.

<details>
<summary><b>Click to expand: Installation from Source</b></summary>

### Prerequisites

- Python 3.7 or higher
- Google Chrome browser
- Basic command line knowledge

### Setup Steps

1. **Get the Code**
   ```bash
   git clone https://github.com/ngocanh54/wikidich_ebook.git
   cd wikidich_ebook
   ```

2. **Install Dependencies** (Automatic Setup)
   ```bash
   # On macOS/Linux:
   python3 setup_local.py

   # On Windows:
   python setup_local.py
   ```

   The setup script will:
   - ✓ Check your Python version
   - ✓ Verify Google Chrome is installed
   - ✓ Install all required packages
   - ✓ Set up ChromeDriver automatically

3. **Launch the GUI**
   ```bash
   # On macOS/Linux:
   python3 gui.py

   # On Windows:
   python gui.py
   ```

</details>

<details>
<summary><b>Click to expand: Command Line Usage</b></summary>

### Basic Commands

**Download a complete novel:**
```bash
python3 main.py "https://truyenwikidich.net/truyen/your-novel-url"
```

**Resume from chapter 100:**
```bash
python3 main.py "https://truyenwikidich.net/truyen/your-novel-url" --start-chapter 100
```

**Just check for new chapters:**
```bash
python3 main.py "https://truyenwikidich.net/truyen/your-novel-url" --check-only
```

**Download chapters only (no EPUB yet):**
```bash
python3 main.py "https://truyenwikidich.net/truyen/your-novel-url" --download-only
```

**Create EPUB from already downloaded chapters:**
```bash
python3 main.py "https://truyenwikidich.net/truyen/your-novel-url" --epub-only
```

> **Note:** Use `python` instead of `python3` on Windows.

</details>

<details>
<summary><b>Click to expand: Python API Usage</b></summary>

### For Python Programmers

**Simple example:**
```python
from wikidich_ebook import download_n_make_ebook_wikidich

# Download and create EPUB
download_n_make_ebook_wikidich(
    url_toc="https://truyenwikidich.net/truyen/your-novel-url",
    latest_chapter_read=0  # Start from beginning
)
```

**Resume from a specific chapter:**
```python
download_n_make_ebook_wikidich(
    url_toc="https://truyenwikidich.net/truyen/your-novel-url",
    latest_chapter_read=100  # Start from chapter 100
)
```

**Control volume organization:**
```python
download_n_make_ebook_wikidich(
    url_toc="https://truyenwikidich.net/truyen/your-novel-url",
    use_volume_structure=True  # Organize by volumes
)
```

### Advanced: Step-by-Step Control

```python
from wikidich_ebook import check_if_updated, get_toc, download_truyen, make_ebook

url = "https://truyenwikidich.net/truyen/your-novel-url"

# Step 1: Check for updates
is_updated, folder = check_if_updated(url)

# Step 2: Get table of contents
get_toc(url, folder)

# Step 3: Download chapters
download_truyen(folder, latest_chapter_read=0)

# Step 4: Create EPUB
make_ebook(folder, latest_chapter_read=0)
```

</details>

<details>
<summary><b>Click to expand: Building macOS App from Source</b></summary>

### Create Your Own DMG Installer

**Prerequisites:**
- macOS 10.13+ (High Sierra or later)
- Python 3.7+
- Xcode Command Line Tools

**Steps:**

1. Install build tools:
   ```bash
   pip install -r requirements-build.txt
   ```

2. Build the app:
   ```bash
   sudo ./build_mac_app.sh
   ```

   Note: `sudo` is needed to clean old builds. Enter your password when prompted.

3. Find your DMG:
   ```bash
   ls dist/*.dmg
   ```

**Output:**
- **App**: `dist/Wikidich Ebook Creator.app` (standalone macOS app)
- **Installer**: `dist/WikidichEbookCreator-{version}.dmg` (~76MB, ready to share)

</details>

---

## ❓ Frequently Asked Questions

<details>
<summary><b>What formats does this create?</b></summary>

It creates EPUB files, which work on:
- iPhones/iPads (Apple Books app)
- Android phones/tablets (Google Play Books, Moon+ Reader, etc.)
- Kindle devices (need to convert using Calibre)
- Computers (Calibre, Adobe Digital Editions, etc.)
- E-readers (Kobo, Nook, etc.)

</details>

<details>
<summary><b>Do I need to know programming?</b></summary>

**No!** If you use the macOS app, just download and click buttons. No coding needed.

If you use the command line or Python API, then yes, basic programming knowledge helps.

</details>

<details>
<summary><b>Can I use this on Windows?</b></summary>

Currently, the standalone app (DMG) is only for macOS.

Windows users can use the Python version:
1. Install Python 3.7+
2. Install Google Chrome
3. Follow the "Installation from Source" instructions above

</details>

<details>
<summary><b>Is this legal?</b></summary>

This tool is for **personal backup and offline reading only**. Always:
- Support the original authors and translators
- Visit the official website
- Respect copyright laws and terms of service

</details>

<details>
<summary><b>What if the download fails?</b></summary>

The tool automatically retries failed downloads. If a chapter consistently fails:
- Check your internet connection
- Make sure the URL is correct
- Try again later (the website might be down)
- Check the log output for error details

</details>

<details>
<summary><b>Can I download just part of a novel?</b></summary>

Yes! Use the "Start Chapter" option in the GUI, or use `--start-chapter` in command line:

```bash
python3 main.py "URL" --start-chapter 100
```

This downloads from chapter 100 onwards.

</details>

<details>
<summary><b>How do I update the app?</b></summary>

**macOS App:**
- The app checks for updates when you open it
- If a new version exists, you'll see a notification
- Click to download the new DMG
- Install the new version (replaces the old one)

**Python Version:**
```bash
git pull
python3 setup_local.py  # Reinstall dependencies
```

</details>

---

## 🎯 How It Works

Behind the scenes, the tool:

1. **Fetches Information** - Gets book title, author, cover image, and chapter list
2. **Downloads Chapters** - Visits each chapter page and saves the content
3. **Creates EPUB** - Packages everything into a proper ebook file with formatting

**Features:**
- ⏱️ Smart delays between downloads (avoids overwhelming the server)
- 🔄 Automatic retry for failed downloads
- 📁 Organizes by volumes if the novel has them
- 💾 Saves progress (skip already downloaded chapters)
- 🎨 Includes custom fonts for better reading experience

---

## 📁 What Gets Created

When you run the tool, it creates a folder with:

```
your-novel-name/
├── info.json                    # Book information
├── toc.csv                      # List of all chapters
├── your-novel-name_bookcover.jpg  # Cover image
├── chap_0001.html              # Chapter 1
├── chap_0002.html              # Chapter 2
├── ...
├── download_log.log            # Download history
└── YourNovelName.epub          # Final ebook! 📚
```

**The EPUB file** is what you want - copy it to your phone/tablet/e-reader!

---

## 🛠️ Troubleshooting

<details>
<summary><b>macOS won't let me open the app</b></summary>

**First time only:**
1. Right-click the app
2. Click "Open"
3. Click "Open" again in the warning dialog

This tells macOS you trust the app. After this, normal double-click works.

</details>

<details>
<summary><b>"ChromeDriver" error messages</b></summary>

**If using Python version:**
- Make sure Google Chrome is installed
- Run `python3 setup_local.py` again
- The script auto-downloads the correct ChromeDriver

**If using macOS app:**
- Make sure Google Chrome is installed on your Mac
- The app manages ChromeDriver automatically

</details>

<details>
<summary><b>Download is very slow</b></summary>

This is normal! The tool:
- Waits 2-7 seconds between chapters (to be nice to the server)
- Downloads hundreds of chapters
- A 300-chapter novel takes ~30-45 minutes

You can see progress in real-time in the app.

</details>

<details>
<summary><b>Some chapters failed to download</b></summary>

The tool will retry automatically. If it still fails:
- Check the chapter URL manually in your browser
- The chapter might not exist or was deleted
- Try running the tool again (it skips already downloaded chapters)

</details>

---

## 🔧 Technical Details

<details>
<summary><b>Click to expand: Technologies Used</b></summary>

- **Python 3.7+** - Main programming language
- **PyQt6** - Modern GUI framework
- **Selenium** - Web automation (controls Chrome browser)
- **BeautifulSoup** - HTML parsing
- **ebooklib** - EPUB file creation
- **pandas** - Data processing
- **webdriver-manager** - Automatic ChromeDriver management

</details>

<details>
<summary><b>Click to expand: Project Structure</b></summary>

```
wikidich_ebook/
├── wikidich_ebook/           # Main package
│   ├── models.py             # Data structures
│   ├── config.py             # Settings
│   ├── scraper.py            # Web scraping
│   ├── parser.py             # HTML parsing
│   ├── downloader.py         # Chapter downloading
│   ├── epub_builder.py       # EPUB creation
│   └── workflow.py           # Main logic
├── gui.py                    # GUI application
├── main.py                   # Command line interface
├── setup_local.py            # Installation script
└── README.md                 # This file
```

</details>

<details>
<summary><b>Click to expand: Configuration</b></summary>

Default settings (in `config.py`):
- **Delay between downloads:** 2-7 seconds (random)
- **Chapters per page:** 501
- **Font:** Playwrite IT Moderna (auto-downloaded)
- **Chrome User Agent:** Latest Chrome version

You can modify these by editing the config file.

</details>

---

## 📝 Version History

### v2.1.0 (Latest)
- ✨ Real-time progress bar showing chapter downloads
- ✨ All CLI options now in GUI
- 🐛 Fixed ChromeDriver compatibility (Chrome 115+)
- 🐛 Fixed volume structure organization
- 🎨 Cleaner log output
- 📚 Improved documentation

[See all releases →](https://github.com/ngocanh54/wikidich_ebook/releases)

---

## 💬 Support & Feedback

- **Bug Reports:** [Open an issue](https://github.com/ngocanh54/wikidich_ebook/issues)
- **Feature Requests:** [Open an issue](https://github.com/ngocanh54/wikidich_ebook/issues)
- **Questions:** [Open a discussion](https://github.com/ngocanh54/wikidich_ebook/discussions)

---

## ⚖️ License & Disclaimer

This project is provided **as-is for personal use only**.

- ✅ Use for personal offline reading
- ✅ Backup your favorite novels
- ❌ Do not redistribute downloaded content
- ❌ Do not use for commercial purposes

**Please support original authors and translators** by visiting [truyenwikidich.net](https://truyenwikidich.net).

---

## 🙏 Credits

- Built with ❤️ for Vietnamese novel readers
- Uses [truyenwikidich.net](https://truyenwikidich.net) as source
- Created with assistance from [Claude Code](https://claude.com/claude-code)

---

**Happy Reading! 📚✨**
