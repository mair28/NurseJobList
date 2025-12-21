"""Debug script to see what's on the NurseFern page."""

import asyncio
from playwright.async_api import async_playwright


async def debug():
    async with async_playwright() as p:
        # Use visible browser for debugging
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("Loading NurseFern...")
        await page.goto("https://app.nursefern.com", wait_until="networkidle", timeout=60000)
        
        print("Waiting 10 seconds for content to load...")
        await page.wait_for_timeout(10000)
        
        # Scroll down
        for i in range(5):
            await page.evaluate("window.scrollBy(0, 500)")
            await page.wait_for_timeout(500)
        
        # Get page content
        content = await page.content()
        print(f"Page length: {len(content)}")
        
        # Find all h4 elements
        h4s = await page.query_selector_all('h4')
        print(f"Found {len(h4s)} h4 elements")
        
        for h4 in h4s[:20]:
            text = await h4.inner_text()
            print(f"  H4: {text[:60]}")
        
        # Find all h5 elements
        h5s = await page.query_selector_all('h5')
        print(f"\nFound {len(h5s)} h5 elements")
        
        for h5 in h5s[:20]:
            text = await h5.inner_text()
            if text.strip():
                print(f"  H5: {text[:60]}")
        
        # Save screenshot
        await page.screenshot(path="nursefern_debug.png")
        print("\nSaved screenshot to nursefern_debug.png")
        
        input("Press Enter to close browser...")
        await browser.close()


asyncio.run(debug())
