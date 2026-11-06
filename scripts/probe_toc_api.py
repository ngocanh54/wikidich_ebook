#!/usr/bin/env python3
"""
Probe: can the chapter list (TOC) be fetched with plain HTTP, without a browser?

The site loads the chapter list from a signed endpoint:
    GET /book/index?bookId=..&start=..&size=..&signKey=..&sign=..
where bookId and signKey sit in an inline script of the book page and
    sign = sha256_hex(rotate(signKey + str(start) + str(size), N))
    rotate(t, N) = t[N:] + t[:N]
N is randomized per page and is written in that page's inline `fuzzySign` function.

This script reproduces the browser's requests with `requests` and reports what happens,
so we can decide whether get_toc() can use HTTP first and keep Playwright as a fallback.
It makes 1 page request plus 1 request per TOC page, with the project's delays between them.
Note: the site limits TOC loads per IP (about ten in a short time). When exhausted, the endpoint
returns HTTP 200 with a notice instead of chapters; this script reports that as INCONCLUSIVE
(exit code 3). Don't run it repeatedly in a loop.

Usage:
    python3 scripts/probe_toc_api.py <BOOK_URL> [--ua app|browser]

    --ua app      send the app's REQUEST_HEADERS (default; this is what the scraper uses today)
    --ua browser  send a regular desktop Chrome user agent, to see if the UA is what gets blocked
"""
import argparse
import hashlib
import os
import random
import re
import sys
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from wikidich_ebook.config import (  # noqa: E402
    CHAPTERS_PER_PAGE, MAX_DELAY, MIN_DELAY, REQUEST_HEADERS, REQUEST_TIMEOUT)

BROWSER_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")
BLOCK_HINTS = ("just a moment", "cf-chl", "captcha", "attention required", "access denied")
# Seen 2026-10-25: after roughly ten TOC loads from one IP the endpoint answers HTTP 200 with
# this notice (~196 bytes) instead of the chapter list: "Access quota exhausted. Log in and
# verify email for more."
QUOTA_MARKER = "Đã hết lượt truy cập"


def rotate(text: str, n: int) -> str:
    return text[n:] + text[:n]


def make_sign(sign_key: str, start: int, size: int, offset: int) -> str:
    return hashlib.sha256(rotate(f"{sign_key}{start}{size}", offset).encode()).hexdigest()


def self_test() -> bool:
    """Check the signing code against a request captured from a real browser session."""
    sign_key = "4658b4d21f36e72f86d35d02636b8d2e256050f59040d1341d1614ddb8f3f7e490c143976b4d3333ff3ef9db5edcfd3e"
    expected = "8e4863fe3b942f34b925e22bf386945735dab36a83ef206612ea353aa8d13df2"
    return make_sign(sign_key, 0, 501, 21) == expected


def parse_page_params(html: str):
    """Return (bookId, signKey, offset), each None if not found."""
    book_id = re.search(r'var\s+bookId\s*=\s*"([^"]+)"', html)
    sign_key = re.search(r'var\s+signKey\s*=\s*"([^"]+)"', html)
    offset = re.search(r'substring\((\d+)\)\s*\+\s*text\.substring\(0,\s*\1\)', html)
    return (book_id.group(1) if book_id else None,
            sign_key.group(1) if sign_key else None,
            int(offset.group(1)) if offset else None)


def describe_failure(resp: requests.Response) -> str:
    body = resp.text[:2000].lower()
    hints = [h for h in BLOCK_HINTS if h in body]
    server = resp.headers.get("server", "?")
    cf = "cf-ray" in {k.lower() for k in resp.headers}
    return (f"status={resp.status_code} server={server} cloudflare_headers={cf} "
            f"block_hints={hints or 'none'} body_start={resp.text[:120]!r}")


def delay():
    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))


class StubPage:
    """Lets the app's existing parser read an HTML string like a Playwright page."""
    def __init__(self, html):
        self._html = html

    def content(self):
        return self._html


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url", help="book (TOC) page URL")
    ap.add_argument("--ua", choices=["app", "browser"], default="app")
    ap.add_argument("--compare", metavar="TOC_CSV",
                    help="compare the result with a toc.csv saved by an earlier run (order, names, urls, volumes)")
    args = ap.parse_args()

    print(f"[0] signing self-test: {'OK' if self_test() else 'FAILED (bug in this script)'}")
    if not self_test():
        return 2

    session = requests.Session()
    session.headers.update(REQUEST_HEADERS)
    if args.ua == "browser":
        session.headers["User-Agent"] = BROWSER_UA
    print(f"    user agent ({args.ua}): {session.headers['User-Agent']}")

    # 1. Book page
    try:
        page = session.get(args.url, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as e:
        print(f"[1] book page: REQUEST FAILED: {type(e).__name__}: {e}")
        return 1
    print(f"[1] book page: status={page.status_code} final_url={page.url} "
          f"redirects={len(page.history)}")
    if page.status_code != 200:
        print("    " + describe_failure(page))
        return 1

    book_id, sign_key, offset = parse_page_params(page.text)
    print(f"[2] parsed from HTML: bookId={book_id} signKey={'<%d chars>' % len(sign_key) if sign_key else None} "
          f"rotation_offset={offset}")
    if not (book_id and sign_key and offset is not None):
        print("    FAIL: could not find bookId / signKey / rotation offset in the page. "
              "Either the page is a block page or the site changed its markup.")
        print("    " + describe_failure(page))
        return 1

    origin = re.match(r"https?://[^/]+", page.url).group(0)
    endpoint = urljoin(origin, "/book/index")
    session.headers["Referer"] = page.url
    session.headers["X-Requested-With"] = "XMLHttpRequest"

    # 2. TOC pages: start with (0, CHAPTERS_PER_PAGE), then follow pagination links
    fragments = []        # (start, size, html)
    seen = set()
    queue = [(0, CHAPTERS_PER_PAGE)]
    while queue:
        start, size = queue.pop(0)
        if (start, size) in seen:
            continue
        seen.add((start, size))
        if fragments:
            delay()
        params = {"bookId": book_id, "start": start, "size": size, "signKey": sign_key,
                  "sign": make_sign(sign_key, start, size, offset)}
        try:
            resp = session.get(endpoint, params=params, timeout=REQUEST_TIMEOUT)
        except requests.RequestException as e:
            print(f"[3] /book/index start={start} size={size}: REQUEST FAILED: {type(e).__name__}: {e}")
            return 1
        soup = BeautifulSoup(resp.text, "html.parser")
        n_links = len(soup.select("a.truncate"))
        print(f"[3] /book/index start={start} size={size}: status={resp.status_code} "
              f"bytes={len(resp.content)} chapter_links={n_links}")
        if resp.status_code != 200:
            print("    " + describe_failure(resp))
            return 1
        if QUOTA_MARKER in resp.text:
            print(f"    QUOTA EXHAUSTED: the site answered 200 with a notice instead of chapters: "
                  f"{BeautifulSoup(resp.text, 'html.parser').get_text(' ', strip=True)!r}")
            print("\nRESULT: INCONCLUSIVE - the TOC quota for this IP is used up. Wait and retry, "
                  "or log in on the site. This is not a signing or user-agent failure.")
            return 3
        fragments.append((start, size, resp.text))
        for a in soup.select("ul.pagination a[data-start]"):
            nxt = (int(a["data-start"]), int(a.get("data-size", size)))
            if nxt not in seen and nxt not in queue:
                queue.append(nxt)

    # 3. Run the app's own parser over the combined fragments
    try:
        from wikidich_ebook.parser import extract_chapters_from_page
        from wikidich_ebook.utils import extract_url_components
    except Exception as e:  # pragma: no cover
        print(f"[4] could not import the app parser ({e}); skipping parity check")
        return 0

    main_page_url, url_pattern = extract_url_components(args.url)
    chapters, per_page = [], []
    for start, size, html in fragments:
        got = extract_chapters_from_page(StubPage(f'<html><body><main><div class="volume-list">{html}</div></main></body></html>'),
                                         url_pattern, main_page_url)
        per_page.append((start, len(got)))
        chapters.extend(got)
    unique = list({(c.chapter_name, c.url): c for c in reversed(chapters)}.values())[::-1]
    volumes = {c.volume_name for c in unique if c.volume_name}

    print(f"[4] app parser: pages={len(fragments)} per_page={per_page} total_unique={len(unique)} "
          f"volumes={len(volumes)}")
    if unique:
        print(f"    first: {unique[0].chapter_name!r} -> {unique[0].url}")
        print(f"    last:  {unique[-1].chapter_name!r} -> {unique[-1].url}")
    ok = bool(unique)
    if args.compare:
        ok = compare_with_csv(unique, args.compare) and ok
    print(f"\nRESULT: {'PASS - plain HTTP can fetch the TOC' if ok else 'FAIL'} "
          f"(ua={args.ua}{', matches ' + args.compare if args.compare and ok else ''})")
    return 0 if ok else 1


def compare_with_csv(chapters, csv_path: str) -> bool:
    """Compare fetched chapters with a toc.csv saved by an earlier (browser-driven) run."""
    import csv
    with open(csv_path, encoding="utf-8") as f:
        expected = list(csv.DictReader(f))
    got = [(c.chapter_name, c.url, c.volume_name or "") for c in chapters]
    exp = [(r["chapter_name"].strip(), r["url"], r["volume_name"] or "") for r in expected]
    print(f"[5] compare with {csv_path}: fetched={len(got)} expected={len(exp)}")
    if got == exp:
        print("    identical: same chapters, same order, same volume assignment")
        return True
    only_got, only_exp = set(got) - set(exp), set(exp) - set(got)
    print(f"    DIFFERENT: only_in_fetched={len(only_got)} only_in_csv={len(only_exp)}")
    for i, (g, e) in enumerate(zip(got, exp)):
        if g != e:
            print(f"    first mismatch at row {i + 1}:\n      fetched: {g}\n      csv:     {e}")
            break
    same_urls = [g[1] for g in got] == [e[1] for e in exp]
    print(f"    urls identical and in order: {same_urls}")
    if same_urls:
        diff_vol = sum(1 for g, e in zip(got, exp) if g[2] != e[2])
        print(f"    rows whose volume differs: {diff_vol}")
    return False


if __name__ == "__main__":
    sys.exit(main())
