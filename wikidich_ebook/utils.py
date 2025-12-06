"""
Utility functions for wikidich ebook creator.
"""
import logging
from typing import Tuple
from urllib.parse import urlparse
from unidecode import unidecode
import requests

from .config import REQUEST_TIMEOUT


def extract_url_components(url: str) -> Tuple[str, str]:
    """
    Extract main page URL and URL pattern from a TOC URL.

    Args:
        url: The table of contents URL

    Returns:
        Tuple of (main_page_url, url_pattern)
    """
    parsed = urlparse(url)
    main_page_url = f"{parsed.scheme}://{parsed.netloc}"
    url_pattern = "-".join(url.split('-')[:-1]) + "/"

    return main_page_url, url_pattern


def create_safe_filename(title: str) -> str:
    """
    Create a filesystem-safe filename from a title.

    Args:
        title: The book title

    Returns:
        Safe filename string
    """
    return unidecode(title).lower().strip().replace(",", "").replace(" ", "-")


def download_image(url: str, output_path: str) -> None:
    """
    Download an image from a URL to a local path.

    Args:
        url: Image URL
        output_path: Local path to save the image
    """
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            f.write(response.content)
        logging.info(f"Downloaded image to {output_path}")
    except requests.RequestException as e:
        logging.error(f"Failed to download image from {url}: {e}")


def download_file(url: str, output_path: str) -> None:
    """
    Download a file from a URL to a local path.

    Args:
        url: File URL
        output_path: Local path to save the file
    """
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            f.write(response.content)
        logging.info(f"Downloaded file to {output_path}")
    except requests.RequestException as e:
        logging.error(f"Failed to download file from {url}: {e}")
        raise
