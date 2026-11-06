"""
Web scraping functions for wikidich ebook creator.
"""
import logging
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from .config import REQUEST_HEADERS, REQUEST_TIMEOUT


class BookLinkError(RuntimeError):
    """The book link could not be opened (site moved, link changed, or no connection)."""


_LINK_HINT = ("The site may have moved or the link may have changed. "
              "Open the book in your browser and copy the link from the address bar.")


def _fetch_book_page(url: str):
    """GET a book page, following redirects, and turn failures into BookLinkError."""
    try:
        response = requests.get(url, headers=REQUEST_HEADERS, stream=True, timeout=REQUEST_TIMEOUT)
    except (requests.ConnectionError, requests.Timeout) as e:
        logging.error(f"Failed to fetch {url}: {e}")
        raise BookLinkError(f"Could not connect to {urlparse(url).netloc}. {_LINK_HINT}") from e
    except requests.RequestException as e:
        logging.error(f"Failed to fetch {url}: {e}")
        raise
    if response.status_code in (404, 410):
        response.close()
        raise BookLinkError(f"The book page was not found (HTTP {response.status_code}). {_LINK_HINT}")
    try:
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Failed to fetch {url}: {e}")
        raise
    return response


def resolve_book_url(url: str) -> str:
    """Return the URL the book page finally lives at after redirects (e.g. after a site move)."""
    response = _fetch_book_page(url)
    final_url = response.url
    response.close()
    if urlparse(final_url).netloc != urlparse(url).netloc:
        print(f"Link redirected to {final_url}")
    return final_url


def get_url_content(url: str, return_url: bool = False):
    """
    Fetch and parse HTML content from a URL.

    Args:
        url: The URL to fetch
        return_url: Also return the final URL after redirects

    Returns:
        BeautifulSoup object with parsed HTML, or (soup, final_url) if return_url

    Raises:
        BookLinkError: If the page is missing or the site cannot be reached
        requests.RequestException: For other request failures
    """
    response = _fetch_book_page(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    return (soup, response.url) if return_url else soup


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
