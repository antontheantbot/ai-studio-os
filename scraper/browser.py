"""
Shared Playwright browser context for all scrapers.
Usage:
    async with get_page() as page:
        await page.goto("https://example.com")
        html = await page.content()
"""
from contextlib import asynccontextmanager
from playwright.async_api import async_playwright, Page


@asynccontextmanager
async def get_page(headless: bool = True) -> Page:
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            args=["--no-sandbox", "--disable-setuid-sandbox"],
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )
        page = await context.new_page()
        try:
            yield page
        finally:
            await browser.close()


async def fetch_html(url: str) -> str:
    """Fetch rendered HTML from a URL."""
    async with get_page() as page:
        await page.goto(url, wait_until="networkidle", timeout=30_000)
        return await page.content()


async def fetch_text(url: str) -> str:
    """Fetch visible text content from a URL."""
    async with get_page() as page:
        await page.goto(url, wait_until="networkidle", timeout=30_000)
        return await page.inner_text("body")
