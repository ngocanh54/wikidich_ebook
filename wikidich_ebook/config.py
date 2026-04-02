"""
Configuration and constants for wikidich ebook creator.
"""

# User agent strings
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.71 Safari/537.36"

REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/120.0.6099.71 Safari/537.36'
}

# Pagination settings
CHAPTERS_PER_PAGE = 501

# Download delays (seconds)
MIN_DELAY = 2
MAX_DELAY = 7

# Font settings
FONT_URL = "https://globalfonts.pro/global_files/66801a2f97374efc5054716d/files/PlaywriteITModerna-Regular.ttf"
FONT_FILENAME = "Playwrite-IT-Moderna-Regular.ttf"
FONT_FAMILY = "Playwrite IT Moderna"

# Google Drive path (for Colab environments)
GDRIVE_BASE_PATH = '/content/drive/MyDrive/TongHopTruyenEpub/'

# Request timeout (seconds)
REQUEST_TIMEOUT = 30

# WebDriver wait time (seconds)
WEBDRIVER_WAIT = 2

# Download retry settings
MAX_DOWNLOAD_RETRIES = 3       # max full passes over failed chapters
CONSECUTIVE_FAIL_LIMIT = 5     # abort if this many chapters fail in a row (IP block signal)
