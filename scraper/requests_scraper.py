"""
Lightweight requests-based scraper for HealthGigHub.
No browser required - uses cloudscraper for Cloudflare and direct API for NurseFern.
"""

import asyncio
import re
import json
import httpx
from datetime import datetime
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

try:
    import cloudscraper
except ImportError:
    cloudscraper = None
    print("Warning: cloudscraper not installed. Run: pip install cloudscraper")

from config import URLS, MAX_JOBS_PER_SITE, PROXY_URL
from formatter import JobFormatter


def to_string(val) -> str:
    """Convert any value to string, handling lists."""
    if val is None:
        return ""
    if isinstance(val, list):
        return ", ".join(str(v) for v in val if v)
    return str(val)


class RequestsRemoteNurseScraper:
    """Scrapes Remote Nurse Connection using requests + cloudscraper."""
    
    def __init__(self):
        self.base_url = URLS["remotenurse"]
        self.session = None
        self.jobs: List[Dict] = []
    
    def scrape(self) -> List[Dict]:
        """Main scraping method."""
        print("\n" + "="*60)
        print("[RemoteNurse-Requests] Starting scrape...")
        print("="*60)
        
        if not cloudscraper:
            print("[RemoteNurse] cloudscraper not available")
            return []
        
        # Create cloudscraper session with browser emulation and proxy
        self.session = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            },
            delay=3
        )
        
        # Set up proxy
        self.session.proxies = {
            'http': PROXY_URL,
            'https': PROXY_URL
        }
        print(f"[RemoteNurse] Using rotating proxy...")
        
        try:
            # Get job board page
            print("[RemoteNurse] Fetching job board...")
            response = self.session.get(self.base_url, timeout=30)
            
            if response.status_code != 200:
                print(f"[RemoteNurse] Failed to fetch page: {response.status_code}")
                return []
            
            # Check if we're still on Cloudflare
            if "Just a moment" in response.text or "challenge" in response.text.lower():
                print("[RemoteNurse] Cloudflare challenge not bypassed. Try using browser mode.")
                return []
            
            print("[RemoteNurse] Page fetched successfully!")
            
            # Parse job links
            soup = BeautifulSoup(response.text, 'lxml')
            job_links = self._get_job_links(soup)
            print(f"[RemoteNurse] Found {len(job_links)} job links")
            
            # Limit jobs
            if MAX_JOBS_PER_SITE > 0:
                job_links = job_links[:MAX_JOBS_PER_SITE]
            
            # Scrape each job
            for i, link in enumerate(job_links, 1):
                print(f"[RemoteNurse] Scraping job {i}/{len(job_links)}...")
                job_data = self._scrape_job(link)
                if job_data:
                    self.jobs.append(job_data)
            
            print(f"[RemoteNurse] Scraped {len(self.jobs)} jobs")
            
        except Exception as e:
            print(f"[RemoteNurse] Error: {e}")
            import traceback
            traceback.print_exc()
        
        return self.jobs
    
    def _get_job_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract job links from the listing page."""
        links = []
        
        # Try multiple selectors
        selectors = [
            "a.job_listing-clickbox",
            "a[href*='/job/']",
            ".jobs-container a",
        ]
        
        for selector in selectors:
            for a in soup.select(selector):
                href = a.get("href", "")
                if href and "/job/" in href and href not in links:
                    if href.startswith("/"):
                        href = "https://remotenurseconnection.com" + href
                    links.append(href)
            
            if links:
                break
        
        return links
    
    def _scrape_job(self, url: str) -> Optional[Dict]:
        """Scrape a single job page."""
        try:
            response = self.session.get(url, timeout=20)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            return {
                "job_title": self._get_text(soup, "h1.entry-title"),
                "company": self._get_text(soup, ".dp-company-info h4"),
                "date_posted": self._get_text(soup, "span.published"),
                "location": self._extract_location(soup),
                "remote_status": self._extract_field(soup, "Remote Status"),
                "employment_type": self._extract_field(soup, "Employment Type"),
                "schedule": self._extract_field(soup, "Schedule"),
                "license_requirements": self._extract_field(soup, "License"),
                "salary_range": self._extract_salary(soup),
                "job_description": self._get_text(soup, ".et_pb_post_content"),
                "apply_link": self._extract_apply_link(soup),
                "specialties": self._extract_specialties(soup),
                "source_site": "Remote Nurse Connection",
                "source_url": url,
                "scraped_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"[RemoteNurse] Error scraping {url}: {e}")
            return None
    
    def _get_text(self, soup: BeautifulSoup, selector: str) -> str:
        elem = soup.select_one(selector)
        return elem.get_text(strip=True) if elem else ""
    
    def _extract_location(self, soup: BeautifulSoup) -> str:
        for elem in soup.select(".et_pb_text_inner"):
            text = elem.get_text(strip=True)
            if text and text.lower() not in ["remote", "hybrid"]:
                if re.search(r'[A-Z][a-z]+,?\s*[A-Z]{2}|United States', text):
                    return text
        return ""
    
    def _extract_field(self, soup: BeautifulSoup, field_name: str) -> str:
        for blurb in soup.select(".et_pb_blurb"):
            header = blurb.select_one(".et_pb_module_header")
            if header and field_name in header.get_text():
                row = blurb.find_parent(class_=re.compile(r'et_pb_row'))
                if row:
                    for span in row.select(".et_pb_code_inner span"):
                        return span.get_text(strip=True)
        return ""
    
    def _extract_salary(self, soup: BeautifulSoup) -> str:
        text = self._get_text(soup, ".et_pb_post_content")
        match = re.search(r'\$[\d,]+(?:\.\d{2})?\s*[-–]\s*\$[\d,]+', text)
        return match.group(0) if match else ""
    
    def _extract_apply_link(self, soup: BeautifulSoup) -> str:
        for btn in soup.select("a.et_pb_button"):
            if "APPLY" in btn.get_text().upper():
                return btn.get("href", "")
        return ""
    
    def _extract_specialties(self, soup: BeautifulSoup) -> str:
        for span in soup.select(".et_pb_code_inner span"):
            text = span.get_text(strip=True)
            if "|" in text or (len(text) > 30 and "," in text):
                if not text.startswith("http") and "$" not in text:
                    return text
        return ""


class RequestsNurseFernScraper:
    """Scrapes NurseFern via their Bubble.io API."""
    
    def __init__(self):
        self.base_url = "https://app.nursefern.com"
        self.jobs: List[Dict] = []
    
    async def scrape(self) -> List[Dict]:
        """Main scraping method using API."""
        print("\n" + "="*60)
        print("[NurseFern-API] Starting scrape...")
        print("="*60)
        
        async with httpx.AsyncClient() as client:
            try:
                # Bubble.io apps typically have their data at specific endpoints
                # Let's try to find the jobs API
                api_urls = [
                    f"{self.base_url}/api/1.1/obj/job",
                    f"{self.base_url}/api/1.1/wf/getjobs",
                    f"{self.base_url}/version-test/api/1.1/obj/job",
                ]
                
                for api_url in api_urls:
                    try:
                        print(f"[NurseFern] Trying API: {api_url}")
                        response = await client.get(api_url, timeout=10)
                        if response.status_code == 200:
                            data = response.json()
                            print(f"[NurseFern] API found! Got {len(data.get('response', {}).get('results', []))} jobs")
                            return self._parse_api_response(data)
                    except:
                        continue
                
                # If API not found, fall back to page scraping
                print("[NurseFern] API not found, trying page scrape...")
                return await self._scrape_page(client)
                
            except Exception as e:
                print(f"[NurseFern] Error: {e}")
        
        return self.jobs
    
    def _parse_api_response(self, data: dict) -> List[Dict]:
        """Parse Bubble.io API response."""
        jobs = []
        results = data.get("response", {}).get("results", [])
        
        for item in results:
            # Skip archived, deleted, or invalid jobs
            status = item.get("Internal Job Status", "")
            if status in ["Archived", "Deleted"]:
                continue
            if item.get("last_checked_status") == 403:
                continue
            
            # Extract job link
            job_link = to_string(item.get("Job Link", ""))
            
            # Try to extract company from job link URL
            company = self._extract_company_from_url(job_link)
            
            # Get location from Must Work From field
            location = to_string(item.get("Must Work From", []))
            
            # Get salary range
            salary_range = item.get("Salary Range", [])
            if isinstance(salary_range, list) and len(salary_range) >= 2:
                min_sal, max_sal = salary_range[0], salary_range[1]
                if max_sal > 0:
                    salary_str = f"${min_sal:,} - ${max_sal:,}"
                else:
                    salary_str = ""
            else:
                salary_str = ""
            
            jobs.append({
                "job_title": to_string(item.get("Job Title", "")),
                "company": company,
                "date_posted": item.get("Created Date", "")[:10] if item.get("Created Date") else "",
                "location": location if location else "Remote",
                "remote_status": "Remote" if location else "",
                "employment_type": self._map_job_type(item.get("Job Type", [])),
                "schedule": "",  # Would need lookup
                "license_requirements": to_string(item.get("Must Work From", [])),
                "salary_range": salary_str,
                "job_description": to_string(item.get("Job Description", "")),
                "apply_link": job_link,
                "specialties": "",
                "source_site": "NurseFern",
                "scraped_at": datetime.now().isoformat()
            })
        
        print(f"[NurseFern] Parsed {len(jobs)} active jobs (filtered archived)")
        return jobs
    
    def _extract_company_from_url(self, url: str) -> str:
        """Try to extract company name from job posting URL."""
        if not url:
            return ""
        
        # Common patterns in job URLs
        import re
        
        # Pattern: company.workdayjobs.com
        match = re.search(r'https?://([^.]+)\.wd\d*\.myworkdayjobs', url)
        if match:
            return match.group(1).replace('-', ' ').title()
        
        # Pattern: jobs.company.com  
        match = re.search(r'https?://jobs?\.([^./]+)\.', url)
        if match:
            return match.group(1).replace('-', ' ').title()
        
        # Pattern: company.jobs/
        match = re.search(r'https?://([^./]+)\.jobs', url)
        if match:
            return match.group(1).replace('-', ' ').title()
        
        # Pattern: careers-company.icims.com
        match = re.search(r'careers-([^.]+)\.icims', url)
        if match:
            return match.group(1).replace('-', ' ').title()
        
        # Generic: take first part of domain if it looks like a company
        match = re.search(r'https?://(?:www\.)?([^./]+)', url)
        if match:
            name = match.group(1)
            # Skip generic domains
            if name not in ['jobs', 'careers', 'apply', 'indeed', 'linkedin', 'glassdoor']:
                return name.replace('-', ' ').title()
        
        return ""
    
    def _map_job_type(self, job_types: list) -> str:
        """Map job type IDs to common values or return empty."""
        # Without access to the lookup API, we just note it exists
        if job_types:
            return "Full-time"  # Default assumption for nursing jobs
        return ""
    
    async def _scrape_page(self, client: httpx.AsyncClient) -> List[Dict]:
        """Fallback: scrape the main page."""
        response = await client.get(self.base_url, timeout=30)
        
        # Look for embedded data in the page
        text = response.text
        
        # Bubble.io often embeds data in script tags
        data_pattern = r'window\.__BUBBLE__\s*=\s*({.*?});'
        match = re.search(data_pattern, text, re.DOTALL)
        
        if match:
            try:
                data = json.loads(match.group(1))
                print(f"[NurseFern] Found embedded data")
                # Parse the embedded data (structure varies)
                return self._parse_embedded_data(data)
            except:
                pass
        
        print("[NurseFern] No API or embedded data found")
        return []
    
    def _parse_embedded_data(self, data: dict) -> List[Dict]:
        """Parse Bubble.io embedded page data."""
        # This would need to be customized based on actual data structure
        return []


async def run_requests_scraper():
    """Run the requests-based scraper."""
    from dedup import filter_new_jobs
    
    all_jobs = []
    
    # Scrape Remote Nurse Connection
    remote_scraper = RequestsRemoteNurseScraper()
    remote_jobs = remote_scraper.scrape()
    all_jobs.extend(remote_jobs)
    
    # Scrape NurseFern
    nursefern_scraper = RequestsNurseFernScraper()
    nursefern_jobs = await nursefern_scraper.scrape()
    all_jobs.extend(nursefern_jobs)
    
    # Filter out jobs we've already seen
    new_jobs = filter_new_jobs(all_jobs)
    
    # Export only new jobs
    if new_jobs:
        formatter = JobFormatter()
        formatter.add_jobs(new_jobs)
        csv_file = formatter.export_csv()
        json_file = formatter.export_json()
        print(f"\n[Output] CSV saved to: {csv_file}")
        print(f"[Output] JSON saved to: {json_file}")
        print(formatter.get_summary())
    else:
        print("\n[Output] No NEW jobs found (all jobs already seen)")


def run_scheduled():
    """Run the scraper (sync wrapper for scheduler)."""
    print(f"\n{'='*60}")
    print(f"Scheduled run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    asyncio.run(run_requests_scraper())


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="HealthGigHub Job Scraper")
    parser.add_argument("--schedule", type=str, help="Run on schedule (e.g., '09:00' for 9 AM daily)")
    parser.add_argument("--once", action="store_true", help="Run once and exit (default)")
    args = parser.parse_args()
    
    if args.schedule:
        import schedule
        import time
        
        print(f"[Scheduler] Starting scheduled scraper at {args.schedule} daily")
        print(f"[Scheduler] Press Ctrl+C to stop")
        
        schedule.every().day.at(args.schedule).do(run_scheduled)
        
        # Run immediately on first start
        run_scheduled()
        
        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        asyncio.run(run_requests_scraper())

