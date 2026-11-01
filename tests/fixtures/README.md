# Test fixtures

These HTML files are **synthetic**: they were written to mirror the selectors that
`wikidich_ebook/parser.py` and `scraper.py` rely on, not captured from the live site.
They prove the code still works with the installed dependency versions, but they cannot
detect that the site changed its markup.

To replace them with real pages, run on a machine that can reach the site:

    python3 scripts/capture_fixtures.py <TOC_URL> <CHAPTER_URL>

Then update the expected values at the top of `tests/offline_check.py`.

| File | Used for |
| --- | --- |
| `toc_volumes.html` | `parse_book_metadata`, `extract_chapters_from_page` with two volumes, plus links that must be excluded |
| `toc_flat.html` | no-`volume-list` fallback and the NaN volume path through pandas |
| `toc_quota.html` | the site's access-quota notice in place of the chapter list (wrapper markup synthetic, notice text real) |
| `chapter_page.html` | `download_chapter_content` paragraph extraction |
| `chapter_blocked.html` | soft block (HTTP 200, no content div) must raise |
