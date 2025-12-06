"""
Main workflow functions for wikidich ebook creator.
"""
import os
import json
import time
import logging
import shutil
from typing import Tuple, List, Optional
from selenium.webdriver.common.by import By
import pandas as pd
from ebooklib import epub

from .models import BookInfo, Chapter
from .scraper import get_url_content, setup_webdriver
from .parser import parse_book_metadata, extract_chapters_from_page
from .downloader import download_chapters, check_multiple_volumes
from .epub_builder import (
    determine_output_title, download_font, create_epub_book,
    add_chapters_to_epub
)
from .utils import extract_url_components, download_image
from .config import CHAPTERS_PER_PAGE, WEBDRIVER_WAIT, FONT_URL, FONT_FILENAME, GDRIVE_BASE_PATH


def check_if_updated(url_toc: str) -> Tuple[bool, str]:
    """
    Check if the book has been updated since last check.

    Args:
        url_toc: URL of the table of contents page

    Returns:
        Tuple of (is_updated, output_folder)
    """
    print(f"Checking: {url_toc}")

    # Fetch and parse metadata
    soup = get_url_content(url_toc)
    book_info = parse_book_metadata(soup, url_toc)

    # Create output folder
    os.makedirs(book_info.output_folder, exist_ok=True)

    # Print book info
    print(f"{book_info.title} - {book_info.author} - {book_info.status}")
    print(f"Latest chapter: {book_info.latest_chapter}")
    print(f"Updated: {book_info.updated_time}")

    # Download book cover if not exists
    cover_path = os.path.join(book_info.output_folder, book_info.bookcover_filename)
    if not os.path.exists(cover_path):
        download_image(book_info.image_url, cover_path)

    # Check if content is updated
    info_file = os.path.join(book_info.output_folder, 'info.json')
    is_updated = True

    if os.path.exists(info_file):
        with open(info_file, 'r', encoding='utf-8') as f:
            old_info = json.load(f)

        if old_info.get('updated_time') == book_info.updated_time:
            is_updated = False
            print("No updates detected.")

    # Save updated info
    if is_updated:
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(book_info.to_dict(), f, ensure_ascii=False, indent=2)
        print("Info saved.")

    return is_updated, book_info.output_folder


def get_toc(url_toc: str, output_folder: str, check_pagination: bool = False,
            page_list: List[int] = None, is_manual: bool = False) -> None:
    """
    Extract table of contents from the book's TOC page.

    Args:
        url_toc: URL of the table of contents
        output_folder: Folder to save the TOC
        check_pagination: Whether to check for pagination
        page_list: List of page numbers (for manual pagination)
        is_manual: Whether pagination is manually specified
    """
    print(f"Getting TOC: {url_toc}")
    main_page_url, url_pattern = extract_url_components(url_toc)

    driver = setup_webdriver()

    try:
        driver.get(url_toc)
        driver.execute_script("location.reload()")
        time.sleep(WEBDRIVER_WAIT)

        # Auto-detect pagination if not manual
        if not is_manual:
            try:
                pagination_elem = driver.find_element(
                    By.XPATH,
                    "//div[@class='volume-list']//div//ul[@class='pagination']"
                )
                page_list = pagination_elem.text.split()
                check_pagination = True
                print(f"Detected {len(page_list)} pages")
            except:
                check_pagination = False
                page_list = []
                print("Single page detected")

        # Collect all chapters
        all_chapters = []

        if check_pagination and page_list:
            for page_num in page_list:
                print(f"Processing page {page_num}")

                # Navigate to page
                try:
                    page_start = CHAPTERS_PER_PAGE * (int(page_num) - 1)
                    xpath = f"//a[@data-start='{page_start}']"
                    chosen_page = driver.find_element(By.XPATH, xpath)

                    driver.execute_script("window.scrollTo(0, 200)")
                    driver.execute_script("arguments[0].click();", chosen_page)
                    driver.execute_script("window.scrollTo(0, 300)")
                    time.sleep(WEBDRIVER_WAIT)
                except Exception as e:
                    logging.warning(f"Could not navigate to page {page_num}: {e}")
                    continue

                # Extract chapters from this page
                chapters = extract_chapters_from_page(driver, url_pattern, main_page_url)
                all_chapters.extend(chapters)

                time.sleep(1)
        else:
            # Single page
            all_chapters = extract_chapters_from_page(driver, url_pattern, main_page_url)

        # Deduplicate and assign chapter numbers
        chapters_dict = {}  # Use dict to remove duplicates by (name, url)

        for chapter in all_chapters:
            key = (chapter.chapter_name, chapter.url)
            if key not in chapters_dict:
                chapters_dict[key] = chapter

        # Sort and assign numbers
        unique_chapters = list(chapters_dict.values())
        unique_chapters.sort(key=lambda c: all_chapters.index(
            next(ch for ch in all_chapters if ch.chapter_name == c.chapter_name and ch.url == c.url)
        ))

        for i, chapter in enumerate(unique_chapters, start=1):
            chapter.chapter_number = i

        print(f"Total chapters found: {len(unique_chapters)}")

        # Export to CSV using pandas (only place pandas is used for processing)
        chapter_dicts = [c.to_dict() for c in unique_chapters]
        df = pd.DataFrame(chapter_dicts)
        csv_path = os.path.join(output_folder, 'toc.csv')
        df.to_csv(csv_path, index=False, encoding='utf-8')
        print(f"TOC saved to {csv_path}")

    finally:
        driver.quit()


def download_truyen(input_dir: str, latest_chapter_read: int = 0, progress_callback=None) -> None:
    """
    Download all chapters of a book.

    Args:
        input_dir: Directory containing book info
        latest_chapter_read: Start from this chapter number
        progress_callback: Optional callback function(current, total) for progress updates
    """
    # Load book info
    info_file = os.path.join(input_dir, "info.json")
    with open(info_file, 'r', encoding='utf-8') as f:
        info_dict = json.load(f)

    print(json.dumps(info_dict, indent=2, ensure_ascii=False))

    book_info = BookInfo.from_dict(info_dict)

    # Load TOC from CSV
    toc_df = pd.read_csv(os.path.join(book_info.output_folder, 'toc.csv'))
    chapters = [
        Chapter(
            chapter_number=int(row['chapter_number']),
            chapter_name=str(row['chapter_name']),
            url=str(row['url']),
            volume_name=str(row['volume_name']) if pd.notna(row.get('volume_name')) else None
        )
        for _, row in toc_df.iterrows()
    ]

    # Check if book has multiple volumes
    has_volumes, volume_count = check_multiple_volumes(chapters)

    if has_volumes:
        print(f"\n📚 This book has {volume_count} volumes!")
        # Show volume distribution
        volume_dist = {}
        for chapter in chapters:
            vol = chapter.volume_name or "No Volume"
            volume_dist[vol] = volume_dist.get(vol, 0) + 1

        print("Volume distribution:")
        for vol_name, count in list(volume_dist.items())[:10]:  # Show first 10 volumes
            print(f"  - {vol_name}: {count} chapters")
        if len(volume_dist) > 10:
            print(f"  ... and {len(volume_dist) - 10} more volumes")
        print()

    # Download with retry
    chapter_prefix = 'chap'
    num_fail = 1

    while num_fail > 0:
        num_fail = download_chapters(
            chapters, chapter_prefix, book_info.title, book_info.author,
            book_info.url_pattern, book_info.output_folder, latest_chapter_read,
            progress_callback
        )

    print("Finish Downloading!")


def make_ebook(input_dir: str, latest_chapter_read: int = 0,
               use_volume_structure: Optional[bool] = None) -> None:
    """
    Create EPUB ebook from downloaded chapters.

    Args:
        input_dir: Directory containing book data
        latest_chapter_read: Starting chapter number
        use_volume_structure: Whether to use volume structure in EPUB TOC.
                             If None (default), auto-detect based on unique volumes.
    """
    # Load book info
    info_file = os.path.join(input_dir, "info.json")
    with open(info_file, 'r', encoding='utf-8') as f:
        info_dict = json.load(f)

    book_info = BookInfo.from_dict(info_dict)

    # Load TOC
    toc_df = pd.read_csv(os.path.join(input_dir, 'toc.csv'))
    latest_chapter = int(toc_df['chapter_number'].max())

    # Load chapters with volume information
    all_chapters = [
        Chapter(
            chapter_number=int(row['chapter_number']),
            chapter_name=str(row['chapter_name']),
            url=str(row['url']),
            volume_name=str(row['volume_name']) if pd.notna(row.get('volume_name')) else None
        )
        for _, row in toc_df.iterrows()
    ]

    # Check if book has meaningful multiple volumes
    has_volumes, volume_count = check_multiple_volumes(all_chapters)

    # Determine whether to use volume structure
    if use_volume_structure is None:
        use_volume_structure = has_volumes  # Auto-detect
    # If user forces yes/no, respect that choice

    if use_volume_structure:
        if has_volumes:
            print(f"📚 Using volume structure ({volume_count} volumes) in EPUB TOC")
        else:
            print("📚 Forcing volume structure in EPUB TOC (user requested)")
    else:
        print("📖 Using flat chapter structure in EPUB TOC")

    # Get list of HTML files
    html_files = sorted([
        f for f in os.listdir(book_info.output_folder)
        if f.endswith('.html') and int(f.split('.')[-2].split('_')[1]) >= latest_chapter_read
    ])

    print(f"{book_info.title} - {book_info.author} ({book_info.status}) - "
          f"Total chapters: {book_info.latest_chapter}")
    print(f"Reading from chapter: {latest_chapter_read}")

    # Determine output title
    output_title = determine_output_title(book_info, latest_chapter, latest_chapter_read)
    output_filename = f"{output_title}.epub"

    # Download font
    font_path = FONT_FILENAME
    download_font(FONT_URL, font_path)

    # Create EPUB book
    book = create_epub_book(book_info, output_title, font_path)

    # Add chapters
    c_list, toc_list = add_chapters_to_epub(book, html_files, book_info.output_folder)

    # Set table of contents (with or without volume structure)
    if use_volume_structure:
        # Create volume-based TOC structure
        chapter_map = {}
        for i, chapter_file in enumerate(html_files):
            try:
                chapter_num = int(chapter_file.split('.')[-2].split('_')[1])
                chapter_obj = next(c for c in all_chapters if c.chapter_number == chapter_num)
                if i < len(c_list):
                    chapter_map[chapter_num] = {
                        'epub_obj': c_list[i],
                        'volume': chapter_obj.volume_name or "Main Story"
                    }
            except (IndexError, ValueError, StopIteration):
                continue

        # Group by volumes
        volume_structure = {}
        for chapter_num in sorted(chapter_map.keys()):
            vol_name = chapter_map[chapter_num]['volume']
            if vol_name not in volume_structure:
                volume_structure[vol_name] = []
            volume_structure[vol_name].append(chapter_map[chapter_num]['epub_obj'])

        # Build nested TOC
        toc_structure = []
        for vol_name, chapters in volume_structure.items():
            toc_structure.append((epub.Section(vol_name), chapters))

        book.toc = toc_structure
        print(f"✓ Created TOC with {len(volume_structure)} volume sections")
    else:
        # Use flat TOC structure
        book.toc = tuple(toc_list)
        print(f"✓ Created flat TOC with {len(toc_list)} chapters")

    # Add navigation
    book.add_item(epub.EpubNcx())
    epub_nav = epub.EpubNav()
    epub_nav.add_link(href='style/stylesheet.css', rel='stylesheet', type='text/css')
    book.add_item(epub_nav)

    # Set spine
    book.spine = ['nav'] + c_list

    # Write EPUB files
    if os.path.exists(output_filename):
        os.remove(output_filename)
    epub.write_epub(output_filename, book, {})
    print(f"Created: {output_filename}")

    # Also save to Google Drive if path exists
    if os.path.exists(GDRIVE_BASE_PATH):
        # Find the created EPUB file
        epub_files = [f for f in os.listdir('.') if f.endswith('.epub')]
        if epub_files:
            latest_epub = max(epub_files, key=os.path.getctime)
            gdrive_dest = os.path.join(GDRIVE_BASE_PATH, latest_epub)

            # Copy to Google Drive
            if os.path.exists(gdrive_dest):
                os.remove(gdrive_dest)
            shutil.copy2(latest_epub, gdrive_dest)
            print(f"✅ Also saved to: {gdrive_dest}")
        else:
            print("⚠️  Warning: Could not find EPUB file to copy to Drive")


def download_n_make_ebook_wikidich(url_toc: str, latest_chapter_read: int = 0,
                                   use_volume_structure: Optional[bool] = None,
                                   progress_callback=None) -> None:
    """
    Complete workflow: check updates, get TOC, download chapters, and create EPUB.

    Args:
        url_toc: URL of the book's table of contents
        latest_chapter_read: Chapter number to start from (0 = start from beginning)
        use_volume_structure: Whether to use volume structure in EPUB TOC.
                             If None (default), auto-detect based on unique volumes.
        progress_callback: Optional callback function(current, total) for progress updates
    """
    try:
        # Check if book has been updated
        is_updated, folder = check_if_updated(url_toc)

        # Get table of contents
        get_toc(url_toc, folder)

        # Download chapters
        download_truyen(folder, latest_chapter_read, progress_callback)

        # Create EPUB
        make_ebook(folder, latest_chapter_read, use_volume_structure)

        print("\n✓ Complete! Your EPUB is ready.")

    except Exception as e:
        logging.error(f"Error in workflow: {e}")
        raise
