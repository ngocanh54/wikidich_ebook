"""
Web scraping functions for wikidich ebook creator.
"""
import logging
import requests
from bs4 import BeautifulSoup

from .config import REQUEST_HEADERS, REQUEST_TIMEOUT


def get_url_content(url: str) -> BeautifulSoup:
    """
    Fetch and parse HTML content from a URL.

    Args:
        url: The URL to fetch

    Returns:
        BeautifulSoup object with parsed HTML

    Raises:
        requests.RequestException: If the request fails
    """
    try:
        response = requests.get(url, headers=REQUEST_HEADERS, stream=True, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except requests.RequestException as e:
        logging.error(f"Failed to fetch {url}: {e}")
        raise


def download_chapter_content(chapter_url: str) -> str:
    """
    Download and extract content from a single chapter.

    Args:
        chapter_url: URL of the chapter

    Returns:
        HTML content of the chapter

    Raises:
        Exception: If chapter cannot be downloaded or parsed
    """
    soup = get_url_content(chapter_url)
    div = soup.body.main.find('div', {'id': 'bookContentBody'})

    if not div:
        raise ValueError("Could not find chapter content")

    # Extract paragraphs
    paragraphs = [str(elem) for elem in div.contents if str(elem).startswith("<p>")]
    return "".join(paragraphs)
