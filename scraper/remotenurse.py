"""
Scraper for Remote Nurse Connection job board.
https://remotenurseconnection.com/remote-nursing-job-board/
"""

import asyncio
import re
from datetime import datetime
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from playwright.async_api import Page

from config import URLS, REMOTENURSE_SELECTORS, MAX_JOBS_PER_SITE, RETRY_ATTEMPTS, RETRY_DELAY
from browser import StealthBrowser, wait_for_cloudflare


class RemoteNurseScraper:
    """Scrapes job listings from Remote Nurse Connection."""
    
    def __init__(self, browser: StealthBrowser):
        self.browser = browser
        self.base_url = URLS["remotenurse"]
        self.jobs: List[Dict] = []
    
    async def scrape(self) -> List[Dict]:
        """Main scraping method. Returns list of job dictionaries."""
        print("\n" + "="*60)
        print("[RemoteNurse] Starting scrape...")
        print("="*60)
        
        page = await self.browser.new_page()
        
        try:
            # Navigate to job board
            await page.goto(self.base_url, wait_until="domcontentloaded")
            
            # Handle Cloudflare if present
            if not await wait_for_cloudflare(page, max_wait=60):
                print("[RemoteNurse] Failed to bypass Cloudflare")
                return []
            
            # Wait additional time for page to fully load after Cloudflare
            print("[RemoteNurse] Waiting for page content to load...")
            await asyncio.sleep(5)
            
            # Try multiple selectors for job listings
            job_selectors = [
                ".job_listing",
                ".job-listing", 
                "article.job_listing",
                "[class*='job']",
                ".et_pb_portfolio_item",
                "a[href*='/job/']"
            ]
            
            job_found = False
            for selector in job_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    print(f"[RemoteNurse] Found jobs using selector: {selector}")
                    job_found = True
                    break
                except:
                    continue
            
            if not job_found:
                print("[RemoteNurse] Could not find job listings on page")
                # Save page HTML for debugging
                content = await page.content()
                print(f"[RemoteNurse] Page title: {await page.title()}")
                print(f"[RemoteNurse] Page has {len(content)} characters")
                return []
            
            # Get all job links
            job_links = await self._get_job_links(page)
            print(f"[RemoteNurse] Found {len(job_links)} job listings")
            
            # Limit jobs if configured
            if MAX_JOBS_PER_SITE > 0:
                job_links = job_links[:MAX_JOBS_PER_SITE]
            
            # Scrape each job
            for i, link in enumerate(job_links, 1):
                print(f"[RemoteNurse] Scraping job {i}/{len(job_links)}: {link[:60]}...")
                
                job_data = await self._scrape_job_page(page, link)
                if job_data:
                    self.jobs.append(job_data)
                
                # Small delay between jobs
                await asyncio.sleep(1)
            
            print(f"[RemoteNurse] Scraped {len(self.jobs)} jobs successfully")
            
        except Exception as e:
            print(f"[RemoteNurse] Error during scrape: {e}")
        finally:
            await page.close()
        
        return self.jobs
    
    async def _get_job_links(self, page: Page) -> List[str]:
        """Extract all job listing URLs from the main page."""
        links = []
        
        # Try multiple selectors for job links
        link_selectors = [
            "a.job_listing-clickbox",
            "a[href*='/job/']",
            "a[href*='/jobs/']", 
            ".job_listing a",
            ".et_pb_portfolio_item a",
            "article a[href]"
        ]
        
        for selector in link_selectors:
            elements = await page.query_selector_all(selector)
            for elem in elements:
                href = await elem.get_attribute("href")
                if href and href.startswith("http") and "/job" in href.lower():
                    if href not in links:
                        links.append(href)
        
        return links
    
    async def _scrape_job_page(self, page: Page, url: str) -> Optional[Dict]:
        """Scrape a single job detail page."""
        for attempt in range(RETRY_ATTEMPTS):
            try:
                await page.goto(url, wait_until="networkidle")
                
                # Wait for content to load
                await page.wait_for_selector("h1.entry-title", timeout=15000)
                
                # Get page content
                content = await page.content()
                soup = BeautifulSoup(content, "lxml")
                
                # Extract job data
                job_data = {
                    "job_title": self._extract_title(soup),
                    "company": self._extract_company(soup),
                    "date_posted": self._extract_date(soup),
                    "location": self._extract_location(soup),
                    "remote_status": self._extract_remote_status(soup),
                    "employment_type": self._extract_employment_type(soup),
                    "schedule": self._extract_schedule(soup),
                    "license_requirements": self._extract_license(soup),
                    "salary_range": self._extract_salary(soup),
                    "job_description": self._extract_description(soup),
                    "apply_link": self._extract_apply_link(soup),
                    "specialties": self._extract_specialties(soup),
                    "source_site": "Remote Nurse Connection",
                    "source_url": url,
                    "scraped_at": datetime.now().isoformat()
                }
                
                return job_data
                
            except Exception as e:
                print(f"[RemoteNurse] Attempt {attempt+1} failed: {e}")
                if attempt < RETRY_ATTEMPTS - 1:
                    await asyncio.sleep(RETRY_DELAY)
        
        return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract job title."""
        elem = soup.select_one("h1.entry-title")
        return elem.get_text(strip=True) if elem else ""
    
    def _extract_company(self, soup: BeautifulSoup) -> str:
        """Extract company name."""
        elem = soup.select_one(".dp-company-info h4")
        return elem.get_text(strip=True) if elem else ""
    
    def _extract_date(self, soup: BeautifulSoup) -> str:
        """Extract date posted."""
        elem = soup.select_one("span.published")
        return elem.get_text(strip=True) if elem else ""
    
    def _extract_location(self, soup: BeautifulSoup) -> str:
        """Extract job location from text elements."""
        # Look in text divs for location
        for elem in soup.select(".et_pb_text_inner"):
            text = elem.get_text(strip=True)
            if text and text not in ["Remote", "Hybrid", "On-site"]:
                # Check if it looks like a location
                if re.search(r'[A-Z][a-z]+,?\s*[A-Z]{2}|United States|Remote', text, re.I):
                    return text
        return ""
    
    def _extract_remote_status(self, soup: BeautifulSoup) -> str:
        """Extract remote work status."""
        # Look for Remote Status header and get its value
        for blurb in soup.select(".et_pb_blurb"):
            header = blurb.select_one(".et_pb_module_header")
            if header and "Remote Status" in header.get_text():
                # Get parent row and find the value in a sibling code block
                row = blurb.find_parent(class_=re.compile(r'et_pb_row'))
                if row:
                    # Find all code_inner spans in this row
                    for span in row.select(".et_pb_code_inner span"):
                        text = span.get_text(strip=True)
                        if text.lower() in ["remote", "hybrid", "on-site", "onsite"]:
                            return text
        
        # Fallback: check text divs
        for elem in soup.select(".et_pb_text_inner"):
            text = elem.get_text(strip=True)
            if text.lower() in ["remote", "hybrid", "on-site"]:
                return text
        
        return ""
    
    def _extract_employment_type(self, soup: BeautifulSoup) -> str:
        """Extract employment type."""
        for blurb in soup.select(".et_pb_blurb"):
            header = blurb.select_one(".et_pb_module_header")
            if header and "Employment Type" in header.get_text():
                row = blurb.find_parent(class_=re.compile(r'et_pb_row'))
                if row:
                    for span in row.select(".et_pb_code_inner span"):
                        text = span.get_text(strip=True)
                        if any(x in text.lower() for x in ["employee", "perm", "contract", "temp"]):
                            return text
        return ""
    
    def _extract_schedule(self, soup: BeautifulSoup) -> str:
        """Extract work schedule."""
        for blurb in soup.select(".et_pb_blurb"):
            header = blurb.select_one(".et_pb_module_header")
            if header and "Schedule" in header.get_text():
                row = blurb.find_parent(class_=re.compile(r'et_pb_row'))
                if row:
                    for span in row.select(".et_pb_code_inner span"):
                        text = span.get_text(strip=True)
                        if any(x in text.lower() for x in ["full", "part", "time", "prn"]):
                            return text
        return ""
    
    def _extract_license(self, soup: BeautifulSoup) -> str:
        """Extract license requirements."""
        for blurb in soup.select(".et_pb_blurb"):
            header = blurb.select_one(".et_pb_module_header")
            if header and "License" in header.get_text():
                row = blurb.find_parent(class_=re.compile(r'et_pb_row'))
                if row:
                    for span in row.select(".et_pb_code_inner span"):
                        text = span.get_text(strip=True)
                        # State abbreviations or license info
                        if re.match(r'^[A-Z]{2}(,\s*[A-Z]{2})*$', text) or "license" in text.lower():
                            return text
        return ""
    
    def _extract_salary(self, soup: BeautifulSoup) -> str:
        """Extract salary information."""
        # Look for salary in description
        desc_elem = soup.select_one(".et_pb_post_content")
        if desc_elem:
            text = desc_elem.get_text()
            # Look for salary patterns
            patterns = [
                r'\$[\d,]+(?:\.\d{2})?\s*[-–]\s*\$[\d,]+(?:\.\d{2})?(?:\s*/\s*(?:hr|hour|year|yr|annually))?',
                r'\$[\d,]+(?:\.\d{2})?\s*(?:per|/)\s*(?:hour|hr|year|yr)',
                r'(?:pay|salary|compensation)[:\s]+\$[\d,]+',
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.I)
                if match:
                    return match.group(0).strip()
        return ""
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract job description."""
        elem = soup.select_one(".et_pb_post_content")
        if elem:
            # Get text content, preserving some structure
            return elem.get_text(separator="\n", strip=True)
        return ""
    
    def _extract_apply_link(self, soup: BeautifulSoup) -> str:
        """Extract the apply link."""
        # Look for apply button
        for btn in soup.select("a.et_pb_button"):
            text = btn.get_text(strip=True).upper()
            if "APPLY" in text:
                href = btn.get("href")
                if href:
                    return href
        
        # Look for company job link
        for elem in soup.select(".dp-additional-link a"):
            href = elem.get("href")
            if href and href.startswith("http"):
                return href
        
        return ""
    
    def _extract_specialties(self, soup: BeautifulSoup) -> str:
        """Extract job specialties/categories."""
        # Specialties are usually in a code block after company info
        for elem in soup.select(".et_pb_code_inner span"):
            text = elem.get_text(strip=True)
            # Check if it looks like specialty tags (comma-separated or pipe-separated)
            if "|" in text or (len(text) > 20 and "," in text):
                if not text.startswith("http") and not "$" in text:
                    return text
        return ""
