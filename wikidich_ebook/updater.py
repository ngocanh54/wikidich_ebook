"""
Auto-update functionality for Wikidich Ebook Creator.
Checks GitHub releases for updates.
"""
import requests
import json
import logging
from packaging import version as version_parser
from typing import Optional, Tuple

from . import __version__


GITHUB_REPO = "ngocanh54/wikidich_ebook"
RELEASES_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def get_latest_version() -> Optional[Tuple[str, str, str]]:
    """
    Check GitHub for the latest release.

    Returns:
        Tuple of (version, download_url, release_notes) or None if check fails
    """
    try:
        response = requests.get(RELEASES_URL, timeout=10)
        response.raise_for_status()
        data = response.json()

        latest_version = data.get('tag_name', '').lstrip('v')
        release_notes = data.get('body', '')

        # Find DMG asset for macOS
        download_url = None
        for asset in data.get('assets', []):
            if asset['name'].endswith('.dmg'):
                download_url = asset['browser_download_url']
                break

        if not download_url:
            # Fallback to release page
            download_url = data.get('html_url', '')

        return (latest_version, download_url, release_notes)

    except Exception as e:
        logging.error(f"Failed to check for updates: {e}")
        return None


def check_for_updates() -> Optional[dict]:
    """
    Check if a new version is available.

    Returns:
        Dictionary with update info if available, None otherwise:
        {
            'available': bool,
            'current_version': str,
            'latest_version': str,
            'download_url': str,
            'release_notes': str
        }
    """
    result = get_latest_version()
    if not result:
        return None

    latest_version, download_url, release_notes = result

    try:
        current = version_parser.parse(__version__)
        latest = version_parser.parse(latest_version)

        return {
            'available': latest > current,
            'current_version': __version__,
            'latest_version': latest_version,
            'download_url': download_url,
            'release_notes': release_notes
        }
    except Exception as e:
        logging.error(f"Failed to parse versions: {e}")
        return None
