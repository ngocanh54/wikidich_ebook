"""
Wikidich Ebook Creator - A tool to download Vietnamese web novels and create EPUB ebooks.
"""

__version__ = "2.1.0"
__author__ = "Anh Nguyen"

# Import main workflow function
from .workflow import (
    download_n_make_ebook_wikidich,
    check_if_updated,
    get_toc,
    download_truyen,
    make_ebook
)

# Import models
from .models import BookInfo, Chapter

# Import key functions that might be useful
from .scraper import get_url_content, download_chapter_content
from .parser import parse_book_metadata, extract_chapters_from_page
from .downloader import download_chapters, check_multiple_volumes, group_chapters_by_volume
from .epub_builder import create_epub_book, add_chapters_to_epub

__all__ = [
    # Main workflow
    'download_n_make_ebook_wikidich',
    'check_if_updated',
    'get_toc',
    'download_truyen',
    'make_ebook',

    # Models
    'BookInfo',
    'Chapter',

    # Scraper
    'get_url_content',
    'download_chapter_content',

    # Parser
    'parse_book_metadata',
    'extract_chapters_from_page',

    # Downloader
    'download_chapters',
    'check_multiple_volumes',
    'group_chapters_by_volume',

    # EPUB Builder
    'create_epub_book',
    'add_chapters_to_epub',
]
