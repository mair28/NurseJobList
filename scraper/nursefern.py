"""
Scraper for NurseFern job board.
https://app.nursefern.com/
"""

import asyncio
import re
from datetime import datetime
from typing import List, Dict, Optional
from playwright.async_api import Page

from config import URLS, MAX_JOBS_PER_SITE, RETRY_ATTEMPTS, RETRY_DELAY
from browser import StealthBrowser


class NurseFernScraper:
    """Scrapes job listings from NurseFern."""
    
    def __init__(self, browser: StealthBrowser):
        self.browser = browser
        self.base_url = URLS["nursefern"]
        self.jobs: List[Dict] = []
    
    async def scrape(self) -> List[Dict]:
        """Main scraping method. Returns list of job dictionaries."""
        print("\n" + "="*60)
        print("[NurseFern] Starting scrape...")
        print("="*60)
        
        page = await self.browser.new_page()
        
        try:
            # Navigate to job board
            await page.goto(self.base_url, wait_until="networkidle")
            
            # Wait for page to fully load (Bubble.io is JS-heavy)
            await asyncio.sleep(3)
            
            # Wait for job cards to appear
            await page.wait_for_selector("[id*='job']", timeout=30000)
            
            # Scroll to load more jobs
            await self._scroll_to_load_all(page)
            
            # Get job count
            job_cards = await page.query_selector_all(".bubble-element.Group")
            job_count = len([c for c in job_cards if await self._is_job_card(c)])
            print(f"[NurseFern] Found {job_count} job cards")
            
            # Limit if configured
            max_jobs = MAX_JOBS_PER_SITE if MAX_JOBS_PER_SITE > 0 else job_count
            
            # Scrape each job by clicking to open popup
            scraped = 0
            job_cards = await page.query_selector_all(".bubble-element.Group")
            
            for card in job_cards:
                if scraped >= max_jobs:
                    break
                
                if not await self._is_job_card(card):
                    continue
                
                scraped += 1
                print(f"[NurseFern] Scraping job {scraped}/{min(max_jobs, job_count)}...")
                
                job_data = await self._scrape_job_popup(page, card)
                if job_data:
                    self.jobs.append(job_data)
                
                await asyncio.sleep(0.5)
            
            print(f"[NurseFern] Scraped {len(self.jobs)} jobs successfully")
            
        except Exception as e:
            print(f"[NurseFern] Error during scrape: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await page.close()
        
        return self.jobs
    
    async def _is_job_card(self, element) -> bool:
        """Check if an element is a job card."""
        try:
            # Job cards have clickable elements and job-related content
            inner_html = await element.inner_html()
            
            # Check for Apply button or job-related keywords
            has_apply = "Apply" in inner_html or "apply" in inner_html
            has_job_content = any(term in inner_html for term in [
                "RN", "Nurse", "REMOTE", "Remote", "HYBRID", "Hybrid",
                "Full-time", "Part-time", "FT", "PT", "LPN", "Case Manager"
            ])
            
            # Also check for specific NurseFern job card class patterns
            has_job_class = "baTaIaVo" in inner_html or "job" in inner_html.lower()
            
            return has_apply and (has_job_content or has_job_class)
        except:
            return False
    
    async def _scroll_to_load_all(self, page: Page, max_scrolls: int = 10):
        """Scroll down to load all jobs (infinite scroll handling)."""
        print("[NurseFern] Scrolling to load all jobs...")
        
        previous_height = 0
        for i in range(max_scrolls):
            # Scroll to bottom
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)
            
            # Check if more content loaded
            current_height = await page.evaluate("document.body.scrollHeight")
            if current_height == previous_height:
                break
            previous_height = current_height
        
        # Scroll back to top
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(0.5)
    
    async def _scrape_job_popup(self, page: Page, card) -> Optional[Dict]:
        """Click a job card and scrape the popup details."""
        for attempt in range(RETRY_ATTEMPTS):
            try:
                # Click the job card to open popup
                await card.click()
                await asyncio.sleep(1)
                
                # Wait for popup to appear
                popup = await page.wait_for_selector("#job-pop-out", timeout=10000)
                
                if popup:
                    job_data = await self._extract_popup_data(page, popup)
                    
                    # Close popup
                    close_btn = await page.query_selector("#job-pop-out button")
                    if close_btn:
                        await close_btn.click()
                        await asyncio.sleep(0.5)
                    else:
                        # Click outside to close
                        await page.keyboard.press("Escape")
                        await asyncio.sleep(0.5)
                    
                    return job_data
                
            except Exception as e:
                print(f"[NurseFern] Attempt {attempt+1} failed: {e}")
                # Try to close any open popup
                try:
                    await page.keyboard.press("Escape")
                    await asyncio.sleep(0.5)
                except:
                    pass
                
                if attempt < RETRY_ATTEMPTS - 1:
                    await asyncio.sleep(RETRY_DELAY)
        
        return None
    
    async def _extract_popup_data(self, page: Page, popup) -> Dict:
        """Extract job data from the popup element."""
        
        # Get popup HTML for parsing
        popup_html = await popup.inner_html()
        
        # Based on actual NurseFern HTML structure:
        # h6.baTaIaVi = date, h4.baTaIaVo = title, h5.baTaIaVu = company
        # Remote tags in .baTaMwv (badge text like "HYBRID", "REMOTE")
        
        job_data = {
            "job_title": await self._get_text(popup, "h4.baTaIaVo"),
            "company": await self._get_text(popup, "h5.baTaIaVu"),
            "date_posted": await self._get_text(popup, "h6.baTaIaVi"),
            "location": await self._extract_field_strong(page, "LOCATION"),
            "remote_status": await self._extract_remote_badges(popup),
            "employment_type": await self._extract_field_strong(page, "JOB TYPE"),
            "schedule": await self._extract_field_strong(page, "SCHEDULE"),
            "license_requirements": await self._extract_license_info(page),
            "salary_range": await self._extract_salary_info(page),
            "job_description": await self._extract_description(popup),
            "apply_link": await self._extract_apply_link(page),
            "specialties": await self._extract_field_strong(page, "SPECIALTIES"),
            "source_site": "NurseFern",
            "source_url": self.base_url,
            "scraped_at": datetime.now().isoformat()
        }
        
        return job_data
    
    async def _get_text(self, element, selector: str) -> str:
        """Get text content from a selector within an element."""
        try:
            elem = await element.query_selector(selector)
            if elem:
                return (await elem.inner_text()).strip()
        except:
            pass
        return ""
    
    async def _extract_field_strong(self, page: Page, field_name: str) -> str:
        """Extract value from a labeled field by finding the strong text after the label."""
        try:
            # Search for the field label text within the popup
            all_text_elements = await page.query_selector_all("#job-pop-out .bubble-element")
            
            found_label = False
            for elem in all_text_elements:
                text = await elem.inner_text()
                text = text.strip()
                
                if field_name.upper() in text.upper():
                    found_label = True
                    # Check if this element contains a strong tag with value
                    strong = await elem.query_selector("strong")
                    if strong:
                        return (await strong.inner_text()).strip()
                    
                    # Check sibling/parent for strong
                    parent = await elem.evaluate_handle("el => el.parentElement")
                    if parent:
                        strong = await parent.query_selector("strong")
                        if strong:
                            return (await strong.inner_text()).strip()
        except Exception as e:
            pass
        return ""
    
    async def _extract_remote_badges(self, popup) -> str:
        """Extract remote status from colored badge tags like HYBRID, REMOTE."""
        try:
            # Look for badges with background-color styling (the colored pills)
            badges = await popup.query_selector_all("h5.baTaMwv, .baTaMwv")
            badge_texts = []
            for badge in badges:
                text = (await badge.inner_text()).strip()
                if text.upper() in ["REMOTE", "HYBRID", "ON-SITE", "TRAVEL", "ONSITE"]:
                    badge_texts.append(text)
            
            if badge_texts:
                return ", ".join(badge_texts)
            
            # Fallback: check any h5 with remote-like text
            h5s = await popup.query_selector_all("h5")
            for h5 in h5s:
                text = (await h5.inner_text()).strip()
                if text.upper() in ["REMOTE", "HYBRID", "ON-SITE"]:
                    return text
        except:
            pass
        return ""
    
    async def _extract_salary_info(self, page: Page) -> str:
        """Extract salary/pay information."""
        try:
            # Check SALARY TRANSPARENCY field
            salary_text = await self._extract_field_strong(page, "SALARY")
            if salary_text and salary_text.lower() not in ["no", "yes"]:
                return salary_text
                
            # If "yes" was found for transparency, look for actual amount
            if salary_text.lower() == "yes":
                # Could expand to look for the actual value nearby
                pass
        except:
            pass
        return ""
    
    async def _extract_license_info(self, page: Page) -> str:
        """Extract license requirements."""
        try:
            license_text = await self._extract_field_value(page, "LICENSE REQUIREMENTS")
            state_text = await self._extract_field_value(page, "Must Be Licensed In")
            
            if license_text and state_text:
                return f"{license_text} ({state_text})"
            return license_text or state_text
        except:
            pass
        return ""
    
    async def _extract_description(self, popup) -> str:
        """Extract job description from popup."""
        try:
            # Find the description section
            desc_elements = await popup.query_selector_all(".bubble-element.Text")
            
            for elem in desc_elements:
                text = await elem.inner_text()
                # Description is usually the longest text block
                if len(text) > 200 and "JOB DESCRIPTION" not in text.upper()[:50]:
                    # Clean up the text
                    text = re.sub(r'\n{3,}', '\n\n', text.strip())
                    return text[:5000]  # Limit length
        except:
            pass
        return ""
    
    async def _extract_apply_link(self, page: Page) -> str:
        """Extract apply link from the Apply button."""
        try:
            # The Apply button may trigger navigation or have a data attribute
            apply_btn = await page.query_selector("#job-pop-out button:has-text('Apply')")
            if apply_btn:
                # Check for onclick or data attributes
                onclick = await apply_btn.get_attribute("onclick")
                if onclick:
                    # Extract URL from onclick
                    match = re.search(r"window\.open\(['\"]([^'\"]+)['\"]", onclick)
                    if match:
                        return match.group(1)
                
                # If clicking opens a new tab, we'd need to capture that
                # For now, note that apply requires interaction
                return "Apply via NurseFern"
        except:
            pass
        return ""
