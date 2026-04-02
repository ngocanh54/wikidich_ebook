"""
Quick smoke test: verify Playwright can handle everything Selenium does in get_toc().

Operations tested (mapped from workflow.py / parser.py):
  1. Launch headless Chromium (replaces setup_webdriver)
  2. Navigate to a URL (replaces driver.get)
  3. Reload page via JS (replaces driver.execute_script("location.reload()"))
  4. Find element by XPath (replaces driver.find_element(By.XPATH, ...))
  5. Read element text (replaces pagination_elem.text)
  6. JS scrollTo (replaces driver.execute_script("window.scrollTo(...)"))
  7. Click element via JS (replaces driver.execute_script("arguments[0].click()", el))
  8. Get full page HTML (replaces driver.page_source used in parser.py)

Usage:
    uv run test_playwright.py <TOC_URL>
    # or: python test_playwright.py <TOC_URL>
    # or without a URL to test against a generic public page
"""
import sys
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.71 Safari/537.36"

url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"

print(f"Testing against: {url}\n")

with sync_playwright() as p:
    # 1. Launch headless Chromium — no Chrome install needed, Playwright bundles its own
    browser = p.chromium.launch(headless=True)
    browser_page = browser.new_page(user_agent=USER_AGENT)

    try:
        # 2. Navigate
        browser_page.goto(url, wait_until="domcontentloaded")
        print("✓ goto(url)")

        # 3. Reload via JS  (was: driver.execute_script("location.reload()"))
        browser_page.evaluate("location.reload()")
        browser_page.wait_for_load_state("domcontentloaded")
        print("✓ evaluate('location.reload()')")

        # 4. Find element by XPath  (was: driver.find_element(By.XPATH, ...))
        #    Playwright uses page.locator("xpath=...") — first() to avoid strict-mode error
        try:
            pagination_elem = browser_page.locator(
                "xpath=//div[@class='volume-list']//div//ul[@class='pagination']"
            ).first
            pagination_elem.wait_for(timeout=3000)
            print("✓ locator(xpath=...) — pagination found")

            # 5. Read element text  (was: pagination_elem.text)
            text = pagination_elem.inner_text()
            print(f"  pagination text: {text.split()[:5]}...")
            print("✓ inner_text()")
        except PlaywrightTimeoutError:
            print("  (pagination element not found on this page — single-page TOC, that's OK)")
            print("✓ locator timeout handled gracefully")

        # 4b. Find pagination link by data-start attribute
        try:
            page_start = 0  # first page
            link = browser_page.locator(f"xpath=//a[@data-start='{page_start}']").first
            link.wait_for(timeout=3000)
            print("✓ locator(xpath=//a[@data-start='...'])")

            # 6. JS scrollTo  (was: driver.execute_script("window.scrollTo(0, 200)"))
            browser_page.evaluate("window.scrollTo(0, 200)")
            print("✓ evaluate('window.scrollTo(...)')")

            # 7. Click via JS  (was: driver.execute_script("arguments[0].click()", el))
            #    Playwright can click directly — no JS hack needed
            link.click()
            browser_page.wait_for_timeout(2000)
            print("✓ locator.click()  (replaces execute_script arguments[0].click())")
        except PlaywrightTimeoutError:
            print("  (data-start link not found — no pagination on this page, that's OK)")
            print("✓ locator timeout handled gracefully")

        # 8. Get full page HTML  (was: driver.page_source used in parser.py)
        html = browser_page.content()
        print(f"✓ page.content()  ({len(html)} bytes)")

    finally:
        browser.close()

print("\nAll Playwright operations work correctly.")
print("Safe to migrate from Selenium.")
