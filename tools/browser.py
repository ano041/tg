from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright
from core.logging_config import logger

def browse(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        text = page.inner_text("body")
        browser.close()
        return text[:6000]

async def browse_async(url):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            text = await page.inner_text("body")
            await browser.close()
            return text[:6000]
    except Exception as e:
        logger.error(f"Browse error for {url}: {e}")
        return f"Error browsing {url}: {str(e)}"