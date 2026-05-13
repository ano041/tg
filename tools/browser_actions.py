import asyncio
import json
from playwright.async_api import async_playwright
from core.logging_config import logger

class BrowserSession:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        logger.info("Browser session started")

    async def stop(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Browser session closed")

    async def goto(self, url):
        await self.page.goto(url, wait_until="domcontentloaded")

    async def click(self, selector):
        await self.page.click(selector)

    async def fill(self, selector, text):
        await self.page.fill(selector, text)

    async def get_text(self):
        return await self.page.inner_text("body")

    async def get_buttons(self):
        buttons = await self.page.evaluate('''() => {
            const els = Array.from(document.querySelectorAll('a, button, input[type="submit"], input[type="button"]'));
            return els.map(el => ({
                tag: el.tagName,
                text: el.textContent?.trim().substring(0, 80) || '',
                id: el.id,
                class: el.className,
                href: el.href || '',
                selector: el.tagName + (el.id ? '#' + el.id : '') + (el.className ? '.' + el.className.split(' ').join('.') : '')
            }));
        }''')
        return buttons[:20]