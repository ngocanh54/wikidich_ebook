"""
Web scraping functions for wikidich ebook creator.
"""
import logging
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from .config import USER_AGENT, REQUEST_HEADERS, REQUEST_TIMEOUT


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


def setup_webdriver(headless: bool = True) -> webdriver.Chrome:
    """
    Set up and return a configured Chrome WebDriver.
    Automatically downloads and manages the correct ChromeDriver version.

    Args:
        headless: Run Chrome in headless mode (default: True)

    Returns:
        Configured Chrome WebDriver instance
    """
    options = Options()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--start-maximized")
    options.add_argument(f"user-agent={USER_AGENT}")

    # Suppress webdriver-manager logs
    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    # Use webdriver-manager to automatically download and manage ChromeDriver
    service = Service(ChromeDriverManager().install())

    return webdriver.Chrome(service=service, options=options)


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
