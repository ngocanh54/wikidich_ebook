"""
EPUB creation functions for wikidich ebook creator.
"""
import os
import codecs
from typing import List, Tuple
from bs4 import BeautifulSoup
from ebooklib import epub

from .models import BookInfo
from .config import FONT_FAMILY
from .utils import download_file


def determine_output_title(book_info: BookInfo, latest_chapter: int,
                          latest_chapter_read: int) -> str:
    """
    Determine the appropriate output title based on book status and progress.

    Args:
        book_info: BookInfo object
        latest_chapter: Latest chapter number available
        latest_chapter_read: Chapter number to start from

    Returns:
        Formatted output title
    """
    status = book_info.status
    title = book_info.title

    if status == 'Hoàn thành' and latest_chapter_read == 0:
        return title
    elif status == 'Hoàn thành' and latest_chapter_read > 0:
        return f"{title} from {latest_chapter_read}"
    elif status != 'Hoàn thành' and latest_chapter_read == 0:
        return f"{title} to {latest_chapter}"
    else:
        return f"{title} - from {latest_chapter_read} to {latest_chapter}"


def download_font(font_url: str, font_path: str) -> None:
    """
    Download font file for EPUB.

    Args:
        font_url: URL of the font file
        font_path: Local path to save the font
    """
    download_file(font_url, font_path)


def create_epub_book(book_info: BookInfo, output_title: str, font_path: str) -> epub.EpubBook:
    """
    Create and configure an EPUB book object.

    Args:
        book_info: BookInfo object
        output_title: Title for the output file
        font_path: Path to the font file

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

    # Add font
    with open(font_path, 'rb') as f:
        font_content = f.read()

    font_item = epub.EpubItem(
        uid="main_font",
        file_name=f"fonts/{os.path.basename(font_path)}",
        media_type="application/vnd.ms-opentype",
        content=font_content
    )
    book.add_item(font_item)

    # Add fonts CSS
    fonts_css_content = f'''
    @font-face {{
      font-family: '{FONT_FAMILY}';
      src: url(../fonts/{os.path.basename(font_path)}) format('truetype');
    }}
    '''
    fonts_css = epub.EpubItem(
        uid="font_embed",
        file_name="style/fonts.css",
        media_type="text/css",
        content=fonts_css_content
    )
    book.add_item(fonts_css)

    # Add stylesheet
    stylesheet_content = f'''
    h1, body {{
      font-family: '{FONT_FAMILY}';
      font-style: normal;
      font-weight: normal;
      font-size: 1em;
    }}
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
            html_raw = ''.join(s for s in f.read() if s.isprintable())

        # Fix font URL
        html_raw = html_raw.replace(
            'https://fonts.googleapis.com/css?family=Playwrite IT Moderna',
            'https://fonts.googleapis.com/css?family=Playwrite+IT+Moderna'
        )

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
