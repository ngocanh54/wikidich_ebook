#!/usr/bin/env python3
"""
Capture real pages into tests/fixtures/ so offline_check.py can detect site markup changes.

Run this from a machine that can reach the site. It makes exactly two page loads: one
rendered TOC page (via Playwright, like get_toc()) and one chapter page (via requests, like
download_chapter_content()).

Usage:
    python3 scripts/capture_fixtures.py <TOC_URL> <CHAPTER_URL>

Then update the expected values at the top of tests/offline_check.py to match the book you
captured, and delete the synthetic note from tests/fixtures/README.md.
"""
import os
import sys

import requests
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from wikidich_ebook.config import REQUEST_HEADERS, REQUEST_TIMEOUT  # noqa: E402

FIXTURES = os.path.join(ROOT, "tests", "fixtures")


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    toc_url, chapter_url = sys.argv[1:]

    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page()
            page.goto(toc_url)
            page.wait_for_load_state("networkidle")
            toc_html = page.content()
        finally:
            browser.close()
    with open(os.path.join(FIXTURES, "toc_volumes.html"), "w", encoding="utf-8") as f:
        f.write(toc_html)

    resp = requests.get(chapter_url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    with open(os.path.join(FIXTURES, "chapter_page.html"), "wb") as f:
        f.write(resp.content)

    print("Wrote toc_volumes.html and chapter_page.html. toc_flat.html and chapter_blocked.html "
          "are still synthetic (they cover fallback paths real pages may not exhibit).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
