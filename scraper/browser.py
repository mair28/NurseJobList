"""
Browser management with Camoufox for anti-bot bypass.
Supports session persistence to maintain Cloudflare cookies.
"""

import asyncio
import os
import json
from pathlib import Path
from camoufox.async_api import AsyncCamoufox
from playwright.async_api import Page, BrowserContext

from config import HEADLESS, TIMEOUT

# Session storage path
SESSION_DIR = Path(__file__).parent / ".sessions"
SESSION_DIR.mkdir(exist_ok=True)


class StealthBrowser:
    """Manages a stealth browser instance using Camoufox for anti-detection."""
    
    def __init__(self, headless: bool = None):
        self.camoufox = None
        self.browser = None
        self.context = None
        self.headless = headless if headless is not None else HEADLESS
    
    async def start(self):
        """Initialize the browser with Camoufox stealth settings."""
        # Use persistent context for session storage
        user_data_dir = str(SESSION_DIR / "browser_data")
        
        self.camoufox = AsyncCamoufox(
            headless=self.headless,
            geoip=True,
            persistent_context=True,
            user_data_dir=user_data_dir,
        )
        
        self.browser = await self.camoufox.start()
        self.context = self.browser
        
        mode = "headless" if self.headless else "visible"
        print(f"[Browser] Started Camoufox ({mode}) with stealth configuration")
        return self
    
    async def new_page(self) -> Page:
        """Create a new page."""
        page = await self.browser.new_page()
        page.set_default_timeout(TIMEOUT)
        return page
    
    async def close(self):
        """Close browser and cleanup."""
        if self.browser:
            await self.browser.close()
        print("[Browser] Closed")


async def wait_for_cloudflare(page: Page, max_wait: int = 60, interactive: bool = False):
    """
    Wait for Cloudflare challenge to complete.
    Uses CapSolver if available and challenge doesn't auto-pass.
    
    Args:
        page: The page to check
        max_wait: Maximum seconds to wait
        interactive: If True, waits longer for manual solving
        
    Returns True if successful, False if timeout.
    """
    print("[Browser] Checking for Cloudflare challenge...")
    
    # First, check if we can pass naturally
    for i in range(15):  # Wait up to 15 seconds for natural pass
        try:
            title = await page.title()
            content = await page.content()
            
            if "Just a moment" not in title and "challenge" not in content.lower():
                print("[Browser] Cloudflare challenge passed!")
                return True
            
            await asyncio.sleep(1)
        except:
            await asyncio.sleep(1)
    
    # If still blocked, try CapSolver
    print("[Browser] Attempting CapSolver for Turnstile...")
    
    try:
        from config import CAPSOLVER_API_KEY
        
        if await solve_turnstile_with_capsolver(page, CAPSOLVER_API_KEY):
            print("[Browser] Cloudflare solved via CapSolver!")
            await asyncio.sleep(3)  # Wait for page to load after solve
            return True
    except ImportError:
        print("[Browser] CapSolver API key not configured")
    except Exception as e:
        print(f"[Browser] CapSolver error: {e}")
    
    # Fallback to waiting
    wait_time = max_wait if not interactive else 120
    
    for i in range(wait_time - 15):  # Already waited 15 seconds
        try:
            title = await page.title()
            content = await page.content()
            
            if "Just a moment" not in title and "checking" not in content.lower():
                print("[Browser] Cloudflare challenge passed!")
                return True
            
            if i % 5 == 0:
                if interactive:
                    print(f"[Browser] Waiting for manual Cloudflare solve... ({i+15}s)")
                else:
                    print(f"[Browser] Waiting for Cloudflare... ({i+15}s)")
            await asyncio.sleep(1)
        except Exception as e:
            await asyncio.sleep(1)
    
    print("[Browser] Cloudflare challenge timeout")
    return False


async def solve_turnstile_with_capsolver(page: Page, api_key: str) -> bool:
    """
    Solve Cloudflare Turnstile using CapSolver API.
    """
    import httpx
    import re
    
    # Get the current page URL
    url = page.url
    
    # Try to find the Turnstile sitekey from the page
    content = await page.content()
    
    # Look for sitekey in various patterns
    sitekey_patterns = [
        r'data-sitekey="([^"]+)"',
        r'sitekey["\']?\s*[:=]\s*["\']([^"\']+)',
        r'turnstile/v0/api\.js\?.*?sitekey=([^&"\']+)',
    ]
    
    sitekey = None
    for pattern in sitekey_patterns:
        match = re.search(pattern, content)
        if match:
            sitekey = match.group(1)
            break
    
    if not sitekey:
        print("[CapSolver] Could not find Turnstile sitekey")
        return False
    
    print(f"[CapSolver] Found sitekey: {sitekey[:20]}...")
    
    # Create task with CapSolver
    create_task_url = "https://api.capsolver.com/createTask"
    get_result_url = "https://api.capsolver.com/getTaskResult"
    
    task_payload = {
        "clientKey": api_key,
        "task": {
            "type": "AntiTurnstileTaskProxyLess",
            "websiteURL": url,
            "websiteKey": sitekey,
        }
    }
    
    async with httpx.AsyncClient() as client:
        # Create task
        response = await client.post(create_task_url, json=task_payload, timeout=30)
        result = response.json()
        
        if result.get("errorId") != 0:
            print(f"[CapSolver] Create task error: {result.get('errorDescription')}")
            return False
        
        task_id = result.get("taskId")
        print(f"[CapSolver] Task created: {task_id}")
        
        # Poll for result
        for _ in range(60):  # Max 60 seconds
            await asyncio.sleep(2)
            
            result_response = await client.post(get_result_url, json={
                "clientKey": api_key,
                "taskId": task_id
            }, timeout=30)
            
            result = result_response.json()
            
            if result.get("status") == "ready":
                token = result.get("solution", {}).get("token")
                if token:
                    print("[CapSolver] Got token, injecting...")
                    
                    # Inject the token into the page
                    await page.evaluate(f'''
                        const callback = window.turnstile?.widgetMap?.values()?.next()?.value?.callback;
                        if (callback) {{
                            callback("{token}");
                        }} else {{
                            // Try to find and set the hidden input
                            const inputs = document.querySelectorAll('input[name="cf-turnstile-response"]');
                            inputs.forEach(input => input.value = "{token}");
                            
                            // Also try the global callback
                            if (window.cfTurnstileCallback) {{
                                window.cfTurnstileCallback("{token}");
                            }}
                        }}
                    ''')
                    
                    await asyncio.sleep(2)
                    return True
            
            elif result.get("status") == "failed":
                print(f"[CapSolver] Task failed: {result.get('errorDescription')}")
                return False
    
    print("[CapSolver] Timeout waiting for solution")
    return False


async def setup_cloudflare_session(url: str):
    """
    Run browser in visible mode to manually solve Cloudflare challenge.
    This saves the session for subsequent headless runs.
    """
    print("\n" + "="*60)
    print("CLOUDFLARE SESSION SETUP")
    print("="*60)
    print("A browser window will open. Please:")
    print("1. Wait for the page to load")
    print("2. Solve any CAPTCHA if required")
    print("3. Once the page loads successfully, close the browser")
    print("="*60 + "\n")
    
    browser = StealthBrowser(headless=False)
    await browser.start()
    
    page = await browser.new_page()
    await page.goto(url, wait_until="domcontentloaded")
    
    # Wait for user to solve CAPTCHA
    success = await wait_for_cloudflare(page, max_wait=120, interactive=True)
    
    if success:
        print("[Setup] Session saved! You can now run in headless mode.")
    else:
        print("[Setup] Failed to establish session.")
    
    await browser.close()
    return success
