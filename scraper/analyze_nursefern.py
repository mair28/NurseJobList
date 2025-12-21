"""Analyze NurseFern page structure using Camoufox."""

import asyncio
from camoufox.async_api import AsyncCamoufox


async def analyze():
    async with AsyncCamoufox(headless=False) as browser:
        page = await browser.new_page()
        
        print("Loading NurseFern...")
        await page.goto("https://app.nursefern.com", timeout=120000)
        
        print("Waiting for content...")
        await asyncio.sleep(12)
        
        # Scroll to load content
        for i in range(8):
            await page.evaluate("window.scrollBy(0, 500)")
            await asyncio.sleep(0.5)
        
        await asyncio.sleep(3)
        
        # Analyze page structure
        analysis = await page.evaluate('''() => {
            const result = {
                h1: document.querySelectorAll('h1').length,
                h2: document.querySelectorAll('h2').length,
                h3: document.querySelectorAll('h3').length,
                h4: document.querySelectorAll('h4').length,
                h5: document.querySelectorAll('h5').length,
                h6: document.querySelectorAll('h6').length,
                div: document.querySelectorAll('div').length,
                bubble_elements: document.querySelectorAll('[class*="bubble-element"]').length,
                clickable: document.querySelectorAll('[class*="clickable"]').length,
                sample_text: []
            };
            
            // Get sample text from visible elements
            const textElements = document.querySelectorAll('span, div, h1, h2, h3, h4, h5, h6');
            const seen = new Set();
            textElements.forEach(el => {
                const text = el.innerText?.trim();
                if (text && text.length > 5 && text.length < 80 && !seen.has(text)) {
                    seen.add(text);
                    result.sample_text.push(text);
                }
            });
            
            return result;
        }''')
        
        print(f"\n=== Page Structure ===")
        print(f"H1: {analysis['h1']}")
        print(f"H2: {analysis['h2']}")
        print(f"H3: {analysis['h3']}")
        print(f"H4: {analysis['h4']}")
        print(f"H5: {analysis['h5']}")
        print(f"H6: {analysis['h6']}")
        print(f"Divs: {analysis['div']}")
        print(f"Bubble elements: {analysis['bubble_elements']}")
        print(f"Clickable: {analysis['clickable']}")
        
        print(f"\n=== Sample Text ({len(analysis['sample_text'])} items) ===")
        for text in analysis['sample_text'][:50]:
            print(f"  - {text[:70]}")


asyncio.run(analyze())
