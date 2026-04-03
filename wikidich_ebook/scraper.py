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
    response = requests.get(chapter_url, headers=REQUEST_HEADERS, stream=True, timeout=REQUEST_TIMEOUT)
    status = response.status_code

    if status != 200:
        retry_after = response.headers.get("Retry-After")
        hint = f" (Retry-After: {retry_after}s)" if retry_after else ""
        raise ValueError(f"HTTP {status}{hint}")

    soup = BeautifulSoup(response.content, 'html.parser')
    div = soup.body.main.find('div', {'id': 'bookContentBody'}) if soup.body and soup.body.main else None

    if not div:
        # Soft block: server returned 200 but no chapter content
        page_title = soup.title.string.strip() if soup.title else "unknown"
        logging.warning(f"HTTP 200 but no content div — page title: '{page_title}' (likely soft block or CAPTCHA)")
        raise ValueError(f"Could not find chapter content (HTTP 200, page: '{page_title}')")

    # Extract paragraphs
    paragraphs = [str(elem) for elem in div.contents if str(elem).startswith("<p>")]
    return "".join(paragraphs)
