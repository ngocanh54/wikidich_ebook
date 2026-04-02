"""
Parsing functions for extracting book metadata and table of contents.
"""
import re
import logging
from typing import Optional, List
from bs4 import BeautifulSoup
from playwright.sync_api import Page

from .models import BookInfo, Chapter
from .utils import extract_url_components, create_safe_filename


def extract_cover_info(soup: BeautifulSoup, key: str) -> Optional[str]:
    """
    Extract information from the cover info section.

    Args:
        soup: BeautifulSoup object of the page
        key: The key to search for (e.g., "Tác giả", "Tình trạng")

    Returns:
        Extracted value or None if not found
    """
    cover_info = soup.find('div', {'class': 'cover-info'})
    if not cover_info:
        return None

    paragraphs = cover_info.find_all('p', {'style': 'margin: 0.9rem 0'})
    for p in paragraphs:
        text = p.get_text()
        if key in text and ':' in text:
            return text.split(":", 1)[1].strip()

    return None


def parse_book_metadata(soup: BeautifulSoup, url_toc: str) -> BookInfo:
    """
    Parse book metadata from the table of contents page.

    Args:
        soup: BeautifulSoup object of the TOC page
        url_toc: URL of the TOC page

    Returns:
        BookInfo object with parsed metadata

    Raises:
        ValueError: If required metadata cannot be extracted
    """
    main_page_url, url_pattern = extract_url_components(url_toc)

    # Extract basic info
    title_tag = soup.find('title')
    if not title_tag:
        raise ValueError("Could not find page title")
    title = title_tag.get_text().split("/")[-1]

    author = extract_cover_info(soup, "Tác giả")
    status = extract_cover_info(soup, "Tình trạng")
    latest_chapter = extract_cover_info(soup, "Mới nhất")
    updated_time = extract_cover_info(soup, "Thời gian đổi mới")

    if not all([author, status, latest_chapter, updated_time]):
        raise ValueError("Could not extract all required metadata")

    # Extract image URL
    img_tag = soup.find('img', {'class': "z-depth-1 materialboxed"})
    if not img_tag or 'src' not in img_tag.attrs:
        raise ValueError("Could not find book cover image")
    image_url = main_page_url + img_tag.attrs['src']

    # Create output folder name
    output_folder = create_safe_filename(title)
    bookcover_filename = f'{output_folder}_bookcover.jpg'

    return BookInfo(
        title=title,
        author=author,
        status=status,
        url_pattern=url_pattern,
        output_folder=output_folder,
        image_url=image_url,
        main_page_url=main_page_url,
        bookcover_filename=bookcover_filename,
        latest_chapter=latest_chapter,
        updated_time=updated_time
    )


def extract_chapters_from_page(page: Page, url_pattern: str,
                               main_page_url: str) -> List[Chapter]:
    """
    Extract chapter links from the current page, including volume information.

    Args:
        page: Playwright Page instance
        url_pattern: Pattern to match chapter URLs
        main_page_url: Base URL of the site

    Returns:
        List of Chapter objects with volume information
    """
    soup = BeautifulSoup(page.content(), 'lxml')

    # Build regex pattern for matching URLs
    pattern = re.compile(f"^({url_pattern.replace(main_page_url, '')})((?!:).)*$")

    chapters = []

    # Find the volume-list container
    volume_list = soup.find('div', {'class': 'volume-list'})

    if not volume_list:
        logging.warning("No volume-list found on page")
        # Fallback: Try to find chapters without volume structure
        links = soup.body.main.find_all('a', {'class': 'truncate'}, href=pattern)
        for link in links:
            chapter = Chapter(
                chapter_number=0,
                chapter_name=link.text.strip(),
                url=link.attrs['href'],
                volume_name=None
            )
            chapters.append(chapter)
        return chapters

    # Find all direct child divs (each div is a volume container)
    volume_containers = volume_list.find_all('div', recursive=False)

    for container in volume_containers:
        current_volume = None

        # Get all direct child divs of this container
        child_divs = container.find_all('div', recursive=False)

        if len(child_divs) >= 2:
            # First div contains the h5 with volume name
            header_div = child_divs[0]
            h5_tag = header_div.find('h5')
            if h5_tag:
                current_volume = h5_tag.get_text().strip()
                logging.info(f"Found volume: {current_volume}")

            # Second div contains the ul with chapters
            chapters_div = child_divs[1]
            ul_tag = chapters_div.find('ul')

            if ul_tag:
                # Find all <li> tags, then get <a> tags inside
                li_tags = ul_tag.find_all('li')
                for li in li_tags:
                    link = li.find('a', {'class': 'truncate'}, href=pattern)
                    if link and link.get('href'):
                        chapter = Chapter(
                            chapter_number=0,  # Will be set later
                            chapter_name=link.text.strip(),
                            url=link.attrs['href'],
                            volume_name=current_volume
                        )
                        chapters.append(chapter)
        else:
            # Fallback: if structure is different, try to find links directly
            links = container.find_all('a', {'class': 'truncate'}, href=pattern)
            for link in links:
                chapter = Chapter(
                    chapter_number=0,
                    chapter_name=link.text.strip(),
                    url=link.attrs['href'],
                    volume_name=current_volume
                )
                chapters.append(chapter)

    logging.info(f"Extracted {len(chapters)} chapters from page")
    if chapters and chapters[0].volume_name:
        logging.info(f"Volume information detected: {len(set(c.volume_name for c in chapters if c.volume_name))} volumes found")

    return chapters
