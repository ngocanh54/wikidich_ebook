"""
Chapter downloading functions for wikidich ebook creator.
"""
import os
import time
import random
import logging
from typing import List, Dict, Tuple
from collections import OrderedDict
from tqdm import tqdm

from .models import Chapter
from .scraper import download_chapter_content
from .config import MIN_DELAY, MAX_DELAY


def create_chapter_html(title: str, author: str, chapter_title: str,
                        chapter_content: str) -> str:
    """
    Create HTML document for a chapter.

    Args:
        title: Book title
        author: Book author
        chapter_title: Chapter title
        chapter_content: Chapter content (HTML)

    Returns:
        Complete HTML document as string
    """
    return f'''
    <html>
        <head>
        <title>{title}</title>
        <link href='https://fonts.googleapis.com/css?family=Playwrite+IT+Moderna' rel='stylesheet'>
        <meta name="author" content="{author}">
        <meta charset="utf-8">
        </head>
        <body>
        <h1>{chapter_title}</h1>
        {chapter_content}
        </body>
    </html>'''


def download_chapters(chapters: List[Chapter], chapter_prefix: str, title: str,
                      author: str, url_pattern: str, output_folder: str,
                      latest_chapter_read: int = 0, progress_callback=None) -> int:
    """
    Download all chapters from the list.

    Args:
        chapters: List of Chapter objects
        chapter_prefix: Prefix for chapter filenames
        title: Book title
        author: Book author
        url_pattern: URL pattern for chapters
        output_folder: Folder to save chapters
        latest_chapter_read: Start from this chapter number
        progress_callback: Optional callback function(current, total) for progress updates

    Returns:
        Number of failed downloads
    """
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(output_folder, "download_log.log")),
            logging.StreamHandler()
        ]
    )

    logging.info(f'Download {title}')

    # Filter chapters
    chapters_to_download = [c for c in chapters if c.chapter_number >= latest_chapter_read]
    total_chapters = len(chapters_to_download)
    num_fail = 0

    print(f"\n📥 Downloading {total_chapters} chapters...\n")

    for idx, chapter in enumerate(chapters_to_download, 1):
        # Update progress callback
        if progress_callback:
            progress_callback(idx, total_chapters)

        chapter_url = f"{url_pattern}{chapter.url.split('/')[-1]}"
        output_file = os.path.join(
            output_folder,
            f"{chapter_prefix}_{chapter.chapter_number:04d}.html"
        )

        # Skip if already downloaded
        if os.path.exists(output_file):
            print(f'[{idx}/{total_chapters}] ⏭️  Skip chapter {chapter.chapter_number}: already exists')
            logging.info(f'Skip chapter {chapter.chapter_number}: already exists')
            continue

        try:
            print(f'[{idx}/{total_chapters}] ⬇️  Downloading chapter {chapter.chapter_number}: {chapter.chapter_name}')
            logging.info(f'Downloading chapter {chapter.chapter_number}: {chapter.chapter_name}')

            content = download_chapter_content(chapter_url)
            html_output = create_chapter_html(title, author, chapter.chapter_name, content)

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_output)

            # Random delay to avoid rate limiting
            time.sleep(random.randint(MIN_DELAY, MAX_DELAY))

        except Exception as e:
            print(f'[{idx}/{total_chapters}] ❌ Failed chapter {chapter.chapter_number}: {e}')
            logging.error(f'Failed to download chapter {chapter.chapter_number}: {e}')
            num_fail += 1

    # Summary
    success_count = total_chapters - num_fail
    print(f"\n✅ Download complete: {success_count}/{total_chapters} chapters successful")
    if num_fail > 0:
        print(f"⚠️  {num_fail} chapters failed")

    return num_fail


def check_multiple_volumes(chapters: List[Chapter]) -> Tuple[bool, int]:
    """
    Check if the book has meaningful multiple volumes.

    Args:
        chapters: List of Chapter objects

    Returns:
        Tuple of (has_multiple_volumes, unique_volume_count)
    """
    # Get all unique volume names (excluding None)
    volume_names = [c.volume_name for c in chapters if c.volume_name]

    if not volume_names:
        return False, 0

    unique_volumes = set(volume_names)

    # If only 1 unique volume name, or if all chapters have the same volume name, skip volume structure
    if len(unique_volumes) <= 1:
        return False, len(unique_volumes)

    logging.info(f"Detected {len(unique_volumes)} unique volumes: {list(unique_volumes)[:5]}...")
    return True, len(unique_volumes)


def group_chapters_by_volume(chapters: List[Chapter]) -> Dict[str, List[Chapter]]:
    """
    Group chapters by their volume names.

    Args:
        chapters: List of Chapter objects

    Returns:
        Dictionary mapping volume names to lists of chapters
    """
    volumes = OrderedDict()

    for chapter in chapters:
        vol_name = chapter.volume_name if chapter.volume_name else "Main Story"

        if vol_name not in volumes:
            volumes[vol_name] = []

        volumes[vol_name].append(chapter)

    return volumes
