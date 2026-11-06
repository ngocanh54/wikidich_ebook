#!/usr/bin/env python3
"""
Offline smoke check for wikidich_ebook.

Runs the real parser, scraper, chapter writer and make_ebook() against the HTML
fixtures in tests/fixtures/, with only the network calls stubbed. Needs no site access.
Exit code is non-zero if any check fails.

Usage:
    python3 tests/offline_check.py [--json results.json]
"""
import argparse
import json
import os
import sys
import tempfile
import traceback
import zipfile
from importlib import metadata
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(ROOT, "tests", "fixtures")
sys.path.insert(0, ROOT)

PACKAGES = ["beautifulsoup4", "lxml", "ebooklib", "pandas", "numpy", "requests",
            "unidecode", "playwright", "PyQt6", "packaging", "pyinstaller"]

# Expected values for the fixtures. Update these when fixtures are replaced with real pages.
VOLUME_URL = "https://truyenwikidich.net/truyen/truyen-thu-nghiem-abc123"
VOLUME_TITLE = "Truyện Thử Nghiệm"
VOLUME_CHAPTERS = 6
VOLUME_COUNT = 2
FLAT_URL = "https://truyenwikidich.net/truyen/truyen-phang-xyz789"
FLAT_TITLE = "Truyện Phẳng"
FLAT_CHAPTERS = 4
CHAPTER_TEXT = "Đây là đoạn văn đầu tiên của chương."
CHAPTER_AD = "Quảng cáo"
CHAPTER_BARE_TEXT = "Văn bản trần"

# Placeholder bytes: ebooklib stores cover and font content without decoding it.
FAKE_COVER = b"\xff\xd8\xff\xd9"
FAKE_FONT = b"\x00\x01\x00\x00fake-font"


def read_fixture(name):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as f:
        return f.read()


class FakeResponse:
    def __init__(self, text, status=200):
        self.content = text.encode("utf-8")
        self.status_code = status
        self.headers = {}
        self.url = ""

    def close(self):
        pass

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.HTTPError(f"HTTP {self.status_code}")


class StubPage:
    """Stands in for a Playwright Page; the parser only calls .content()."""
    def __init__(self, html):
        self._html = html

    def content(self):
        return self._html


def build_book(toc_fixture, toc_url):
    """Mirror get_toc() + download_chapters() for a fixture, writing into the cwd."""
    import pandas as pd
    from bs4 import BeautifulSoup
    from wikidich_ebook import scraper
    from wikidich_ebook.downloader import create_chapter_html
    from wikidich_ebook.parser import parse_book_metadata, extract_chapters_from_page

    html = read_fixture(toc_fixture)
    info = parse_book_metadata(BeautifulSoup(html, "html.parser"), toc_url)
    chapters = extract_chapters_from_page(StubPage(html), info.url_pattern, info.main_page_url)

    # Same dedupe and numbering as workflow.get_toc()
    seen = {}
    for c in chapters:
        seen.setdefault((c.chapter_name, c.url), c)
    unique = list(seen.values())
    for i, c in enumerate(unique, start=1):
        c.chapter_number = i

    os.makedirs(info.output_folder, exist_ok=True)
    with open(os.path.join(info.output_folder, "info.json"), "w", encoding="utf-8") as f:
        json.dump(info.to_dict(), f, ensure_ascii=False)
    pd.DataFrame([c.to_dict() for c in unique]).to_csv(
        os.path.join(info.output_folder, "toc.csv"), index=False, encoding="utf-8")
    with open(os.path.join(info.output_folder, info.bookcover_filename), "wb") as f:
        f.write(FAKE_COVER)

    chapter_page = read_fixture("chapter_page.html")
    with mock.patch.object(scraper.requests, "get", lambda *a, **k: FakeResponse(chapter_page)):
        for c in unique:
            content = scraper.download_chapter_content(c.url)
            with open(os.path.join(info.output_folder, f"chap_{c.chapter_number:04d}.html"),
                      "w", encoding="utf-8") as f:
                f.write(create_chapter_html(info.title, info.author, c.chapter_name, content))
    return info, unique


def run_make_ebook(info, use_volume_structure):
    """Run the real make_ebook() with only the font download stubbed."""
    from wikidich_ebook import workflow

    def fake_font(url, path):
        with open(path, "wb") as f:
            f.write(FAKE_FONT)

    with mock.patch.object(workflow, "download_font", fake_font):
        workflow.make_ebook(info.output_folder, 0, use_volume_structure)


def inspect_epub(path, expected_title, expected_chapters):
    import ebooklib
    from ebooklib import epub

    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None, "corrupt zip member"
        first = z.infolist()[0]
        assert first.filename == "mimetype", f"first entry is {first.filename!r}, not 'mimetype'"
        assert first.compress_type == zipfile.ZIP_STORED, "mimetype must be stored uncompressed"
        assert z.read("mimetype") == b"application/epub+zip"
        names = z.namelist()
        assert any(n.endswith(".ttf") for n in names), "embedded font missing"
        assert any(n.endswith("stylesheet.css") for n in names), "stylesheet missing"
        chap1 = next((n for n in names if n.endswith("chap_0001.xhtml")), None)
        assert chap1, "chap_0001.xhtml missing"
        text = z.read(chap1).decode("utf-8")
        assert CHAPTER_TEXT in text, "Vietnamese chapter text lost"
        assert CHAPTER_AD not in text, "non-paragraph content leaked into chapter"
        assert CHAPTER_BARE_TEXT not in text, "bare text node leaked into chapter"

    book = epub.read_epub(path)
    title = book.get_metadata("DC", "title")[0][0]
    assert title == expected_title, f"title {title!r} != {expected_title!r}"
    docs = [i for i in book.get_items_of_type(ebooklib.ITEM_DOCUMENT)
            if os.path.basename(i.file_name).startswith("chap_")]
    assert len(docs) == expected_chapters, f"{len(docs)} chapter documents != {expected_chapters}"
    assert book.get_metadata("DC", "language")[0][0] == "vi"
    return book


def count_leaves(toc):
    n = 0
    for entry in toc:
        if isinstance(entry, (tuple, list)):
            n += count_leaves(entry[1] if isinstance(entry, tuple) else entry)
        else:
            n += 1
    return n


# ── checks ────────────────────────────────────────────────────────────────────

CHECKS = []


def check(fn):
    CHECKS.append(fn)
    return fn


@check
def metadata_parses():
    from bs4 import BeautifulSoup
    from wikidich_ebook.parser import parse_book_metadata
    info = parse_book_metadata(BeautifulSoup(read_fixture("toc_volumes.html"), "html.parser"), VOLUME_URL)
    assert info.title == VOLUME_TITLE, info.title
    assert info.author == "Nguyễn Văn A", info.author
    assert info.status == "Hoàn thành", info.status
    assert info.updated_time == "2026-01-01 10:00", info.updated_time
    assert info.output_folder == "truyen-thu-nghiem", info.output_folder
    assert info.url_pattern == "https://truyenwikidich.net/truyen/truyen-thu-nghiem/", info.url_pattern
    assert info.image_url == "https://truyenwikidich.net/files/cover.jpg", info.image_url


@check
def link_errors_are_friendly():
    import requests
    from wikidich_ebook import BookLinkError
    from wikidich_ebook.scraper import get_url_content
    with mock.patch("requests.get", side_effect=requests.ConnectionError("reset")):
        try:
            get_url_content("https://old.example/truyen/x")
        except BookLinkError as e:
            assert "copy the link" in str(e), e
        else:
            raise AssertionError("connection error not turned into BookLinkError")
    resp = FakeResponse("nope", status=404)
    with mock.patch("requests.get", return_value=resp):
        try:
            get_url_content("https://new.example/truyen/x")
        except BookLinkError as e:
            assert "404" in str(e), e
        else:
            raise AssertionError("404 not turned into BookLinkError")


@check
def redirect_host_is_followed():
    from wikidich_ebook import check_if_updated
    from wikidich_ebook.scraper import resolve_book_url
    resp = FakeResponse(read_fixture("toc_volumes.html"))
    resp.url = "https://moved.example/truyen/truyen-thu-nghiem-abc123"
    with mock.patch("requests.get", return_value=resp):
        assert resolve_book_url("https://old.example/truyen/truyen-thu-nghiem-abc123") == resp.url
        with tempfile.TemporaryDirectory() as tmp:
            cwd = os.getcwd(); os.chdir(tmp)
            try:
                check_if_updated("https://old.example/truyen/truyen-thu-nghiem-abc123")
                import json
                with open(os.path.join("truyen-thu-nghiem", "info.json"), encoding="utf-8") as f:
                    info = json.load(f)
            finally:
                os.chdir(cwd)
    assert info["main_page_url"] == "https://moved.example", info["main_page_url"]
    assert info["url_pattern"].startswith("https://moved.example/"), info["url_pattern"]


@check
def metadata_missing_field_raises():
    from bs4 import BeautifulSoup
    from wikidich_ebook.parser import parse_book_metadata
    broken = read_fixture("toc_volumes.html").replace("Tác giả:", "Không có:")
    try:
        parse_book_metadata(BeautifulSoup(broken, "html.parser"), VOLUME_URL)
    except ValueError:
        return
    raise AssertionError("ValueError not raised when author is missing")


@check
def toc_with_volumes():
    from wikidich_ebook.parser import extract_chapters_from_page
    chapters = extract_chapters_from_page(
        StubPage(read_fixture("toc_volumes.html")),
        "https://truyenwikidich.net/truyen/truyen-thu-nghiem/", "https://truyenwikidich.net")
    assert len(chapters) == VOLUME_CHAPTERS, f"{len(chapters)} chapters != {VOLUME_CHAPTERS}"
    assert not any(":" in c.url or "sach-khac" in c.url for c in chapters), "excluded link was extracted"
    assert chapters[0].volume_name == "Quyển 1: Khởi đầu", chapters[0].volume_name
    assert chapters[-1].volume_name == "Quyển 2: Kết thúc", chapters[-1].volume_name
    assert len({c.volume_name for c in chapters}) == VOLUME_COUNT


@check
def toc_flat_fallback():
    from wikidich_ebook.parser import extract_chapters_from_page
    chapters = extract_chapters_from_page(
        StubPage(read_fixture("toc_flat.html")),
        "https://truyenwikidich.net/truyen/truyen-phang/", "https://truyenwikidich.net")
    assert len(chapters) == FLAT_CHAPTERS, f"{len(chapters)} chapters != {FLAT_CHAPTERS}"
    assert all(c.volume_name is None for c in chapters)


@check
def chapter_content_extracted():
    from wikidich_ebook import scraper
    with mock.patch.object(scraper.requests, "get", lambda *a, **k: FakeResponse(read_fixture("chapter_page.html"))):
        out = scraper.download_chapter_content("https://truyenwikidich.net/x")
    assert out.startswith("<p>" + CHAPTER_TEXT), out[:80]
    assert out.count("<p>") == 3, f"{out.count('<p>')} paragraphs != 3"
    assert CHAPTER_AD not in out and CHAPTER_BARE_TEXT not in out


@check
def chapter_soft_block_raises():
    from wikidich_ebook import scraper
    with mock.patch.object(scraper.requests, "get", lambda *a, **k: FakeResponse(read_fixture("chapter_blocked.html"))):
        try:
            scraper.download_chapter_content("https://truyenwikidich.net/x")
        except ValueError as e:
            assert "Just a moment" in str(e), str(e)
            return
    raise AssertionError("ValueError not raised for a 200 page without content")


@check
def chapter_http_error_raises():
    from wikidich_ebook import scraper
    with mock.patch.object(scraper.requests, "get", lambda *a, **k: FakeResponse("", status=429)):
        try:
            scraper.download_chapter_content("https://truyenwikidich.net/x")
        except ValueError as e:
            assert "429" in str(e), str(e)
            return
    raise AssertionError("ValueError not raised for HTTP 429")


@check
def epub_volume_structure():
    info, chapters = build_book("toc_volumes.html", VOLUME_URL)
    run_make_ebook(info, True)
    book = inspect_epub(f"{VOLUME_TITLE}.epub", VOLUME_TITLE, VOLUME_CHAPTERS)
    assert len(book.toc) == VOLUME_COUNT, f"{len(book.toc)} top-level TOC entries != {VOLUME_COUNT}"
    assert count_leaves(book.toc) >= VOLUME_CHAPTERS, "chapters missing from nested TOC"


@check
def epub_auto_detects_volumes():
    # use_volume_structure=None must detect the two volumes from toc.csv
    info = build_book("toc_volumes.html", VOLUME_URL)[0]
    run_make_ebook(info, None)
    book = inspect_epub(f"{VOLUME_TITLE}.epub", VOLUME_TITLE, VOLUME_CHAPTERS)
    assert len(book.toc) == VOLUME_COUNT, f"auto-detect gave {len(book.toc)} TOC entries"


@check
def epub_forced_flat_structure():
    info = build_book("toc_volumes.html", VOLUME_URL)[0]
    run_make_ebook(info, False)
    book = inspect_epub(f"{VOLUME_TITLE}.epub", VOLUME_TITLE, VOLUME_CHAPTERS)
    assert len(book.toc) == VOLUME_CHAPTERS, f"flat TOC has {len(book.toc)} entries"


@check
def epub_flat_book_with_nan_volumes():
    # volume_name is empty in toc.csv -> NaN through pandas; must not become the string "nan"
    info = build_book("toc_flat.html", FLAT_URL)[0]
    run_make_ebook(info, None)
    book = inspect_epub(f"{FLAT_TITLE} to chap {FLAT_CHAPTERS}.epub",
                        f"{FLAT_TITLE} to chap {FLAT_CHAPTERS}", FLAT_CHAPTERS)
    assert len(book.toc) == FLAT_CHAPTERS, f"{len(book.toc)} TOC entries != {FLAT_CHAPTERS}"


class FakeLocator:
    def __init__(self, page, selector):
        self._page, self._selector = page, selector

    @property
    def first(self):
        return self

    def wait_for(self, timeout=None):
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        if not self._page.pagination_text:
            raise PlaywrightTimeoutError("no pagination bar")

    def inner_text(self):
        return self._page.pagination_text

    def click(self):
        self._page.clicks.append(self._selector)


class FakePage:
    """Minimal Playwright Page for get_toc(): records clicks, serves one HTML document."""
    def __init__(self, html, pagination_text=""):
        self._html, self.pagination_text, self.clicks = html, pagination_text, []

    def goto(self, *a, **k): pass
    def evaluate(self, *a, **k): pass
    def wait_for_load_state(self, *a, **k): pass
    def wait_for_timeout(self, *a, **k): pass
    def locator(self, selector): return FakeLocator(self, selector)
    def content(self): return self._html


def run_get_toc(page, folder="book"):
    """Run the real get_toc() against a FakePage; returns the folder path."""
    from wikidich_ebook import workflow

    class _Browser:
        def new_page(self, **k): return page
        def close(self): pass

    class _Playwright:
        class chromium:
            @staticmethod
            def launch(**k): return _Browser()

    class _Ctx:
        def __enter__(self): return _Playwright()
        def __exit__(self, *a): return False

    os.makedirs(folder, exist_ok=True)
    with mock.patch.object(workflow, "sync_playwright", lambda: _Ctx()), \
         mock.patch.object(workflow, "_ensure_playwright_browser", lambda: None), \
         mock.patch.object(workflow, "resolve_book_url", lambda u: u):
        workflow.get_toc(VOLUME_URL, folder)
    return folder


@check
def toc_quota_notice_raises():
    from wikidich_ebook.parser import extract_chapters_from_page, TocQuotaError
    try:
        extract_chapters_from_page(StubPage(read_fixture("toc_quota.html")),
                                   "https://wikicv.org/truyen/truyen-thu-nghiem/", "https://wikicv.org")
    except TocQuotaError as e:
        assert "quota" in str(e).lower(), str(e)
        return
    raise AssertionError("TocQuotaError not raised for the quota notice")


@check
def get_toc_quota_keeps_existing_toc():
    from wikidich_ebook.parser import TocQuotaError
    os.makedirs("book")
    with open("book/toc.csv", "w", encoding="utf-8") as f:
        f.write("chapter_number,chapter_name,url,volume_name\n1,Old,/truyen/x/old,\n")
    try:
        run_get_toc(FakePage(read_fixture("toc_quota.html")))
    except TocQuotaError:
        with open("book/toc.csv", encoding="utf-8") as f:
            assert "Old" in f.read(), "existing toc.csv was overwritten"
        return
    raise AssertionError("get_toc did not raise TocQuotaError")


@check
def get_toc_empty_list_not_written():
    page = FakePage("<html><body><main><div class='volume-list'></div></main></body></html>")
    try:
        run_get_toc(page)
    except ValueError as e:
        assert not os.path.exists("book/toc.csv"), "empty toc.csv was written"
        assert "No chapters" in str(e), str(e)
        return
    raise AssertionError("ValueError not raised for an empty chapter list")


@check
def get_toc_single_page_writes_csv():
    import pandas as pd
    run_get_toc(FakePage(read_fixture("toc_volumes.html")))
    df = pd.read_csv("book/toc.csv")
    assert len(df) == VOLUME_CHAPTERS, f"{len(df)} rows != {VOLUME_CHAPTERS}"
    assert list(df["chapter_number"]) == list(range(1, VOLUME_CHAPTERS + 1))


@check
def get_toc_does_not_reclick_page_one():
    page = FakePage(read_fixture("toc_volumes.html"), pagination_text="1 2")
    run_get_toc(page)
    assert page.clicks == ["xpath=//a[@data-start='501']"], f"clicks were {page.clicks}"


def versions():
    out = {"python": sys.version.split()[0]}
    for name in PACKAGES:
        try:
            out[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            out[name] = None
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", help="write results as JSON to this path")
    args = ap.parse_args()

    results = []
    start_cwd = os.getcwd()
    with tempfile.TemporaryDirectory(prefix="wikidich_offline_") as tmp:
        for fn in CHECKS:
            workdir = tempfile.mkdtemp(dir=tmp)
            os.chdir(workdir)
            try:
                fn()
                results.append({"check": fn.__name__, "passed": True, "detail": ""})
                print(f"PASS  {fn.__name__}")
            except Exception as e:
                detail = f"{type(e).__name__}: {e}"
                results.append({"check": fn.__name__, "passed": False, "detail": detail})
                print(f"FAIL  {fn.__name__}\n      {detail}")
                if not isinstance(e, AssertionError):
                    traceback.print_exc(limit=4)
            finally:
                os.chdir(start_cwd)

    failed = [r for r in results if not r["passed"]]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({"versions": versions(), "results": results}, f, ensure_ascii=False, indent=2)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
