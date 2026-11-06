"""
EPUB creation functions for wikidich ebook creator.
"""
import os
import codecs
from typing import List, Tuple
from bs4 import BeautifulSoup
from ebooklib import epub

from .models import BookInfo


def determine_output_title(book_info: BookInfo, actual_last_chapter: int,
                          latest_chapter_read: int, total_chapters: int) -> str:
    """
    Determine the appropriate output title based on book status and progress.

    Args:
        book_info: BookInfo object
        actual_last_chapter: Last chapter number actually downloaded
        latest_chapter_read: Chapter number started from (0 = beginning)
        total_chapters: Total chapters in the novel (from TOC)

    Returns:
        Formatted output title
    """
    title = book_info.title
    is_complete_novel = book_info.status == 'Hoàn thành'
    is_full_download = actual_last_chapter >= total_chapters

    if is_complete_novel and is_full_download and latest_chapter_read == 0:
        return title
    elif latest_chapter_read == 0:
        return f"{title} to chap {actual_last_chapter}"
    else:
        return f"{title} chap {latest_chapter_read}-{actual_last_chapter}"


def create_epub_book(book_info: BookInfo, output_title: str) -> epub.EpubBook:
    """
    Create and configure an EPUB book object.

    Args:
        book_info: BookInfo object
        output_title: Title for the output file

    Returns:
        Configured EpubBook object
    """
    book = epub.EpubBook()

    # Set metadata
    book.set_title(output_title)
    book.add_author(book_info.author)

    # Set cover
    cover_path = os.path.join(book_info.output_folder, book_info.bookcover_filename)
    with open(cover_path, 'rb') as f:
        book.set_cover(book_info.bookcover_filename, f.read())

    book.set_language('vi')
    book.add_metadata(None, 'meta', '-epub-media-overlay-active', {'property': 'media:active-class'})

    # Single stylesheet linked by every chapter. No embedded font: the reader's own font is used.
    stylesheet_content = '''
    h1, body {
      font-style: normal;
      font-weight: normal;
      font-size: 1em;
    }
    '''
    stylesheet_css = epub.EpubItem(
        uid="stylesheet",
        file_name="style/stylesheet.css",
        media_type="text/css",
        content=stylesheet_content
    )
    book.add_item(stylesheet_css)

    return book


def add_chapters_to_epub(book: epub.EpubBook, html_files: List[str],
                         output_folder: str) -> Tuple[List, List]:
    """
    Add chapter HTML files to EPUB book.

    Args:
        book: EpubBook object
        html_files: List of HTML file paths
        output_folder: Folder containing the HTML files

    Returns:
        Tuple of (chapter_list, toc_list)
    """
    c_list = []
    toc_list = []

    for html_file in html_files:
        file_path = os.path.join(output_folder, html_file)

        # Read and clean HTML
        with codecs.open(file_path, 'r', encoding='utf-8') as f:
            html_raw = ''.join(s for s in f.read() if s.isprintable() or s in '\n\t')

        html_soup = BeautifulSoup(html_raw, 'html.parser')
        chapter_title = html_soup.find('h1').text
        chapter_num = int(html_file.split('.')[-2].split('_')[1])

        # Create EPUB chapter
        chapter = epub.EpubHtml(
            uid=f"c_{chapter_num:04d}",
            title=chapter_title,
            file_name=f"chap_{chapter_num:04d}.xhtml",
            content=str(html_soup),
            lang='vi',
        )
        chapter.add_link(href='style/stylesheet.css', rel='stylesheet', type='text/css')

        book.add_item(chapter)
        c_list.append(chapter)
        toc_list.append(epub.Link(
            f"chap_{chapter_num:04d}.xhtml",
            chapter_title,
            f"chap_{chapter_num:04d}"
        ))

    return c_list, toc_list
