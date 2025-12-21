"""
NurseFern scraper using Camoufox browser automation.
Uses correct selectors identified from DOM analysis.
"""

import asyncio
import re
from datetime import datetime
from typing import List, Dict

from camoufox.async_api import AsyncCamoufox


class NurseFernScraper:
    """Scrapes NurseFern job board using Camoufox."""
    
    def __init__(self):
        self.base_url = "https://app.nursefern.com"
        self.jobs: List[Dict] = []
    
    async def scrape(self, headless: bool = True) -> List[Dict]:
        """Main scraping method."""
        print("\n" + "="*60)
        print("[NurseFern] Starting scrape...")
        print("="*60)
        
        async with AsyncCamoufox(headless=headless) as browser:
            page = await browser.new_page()
            
            try:
                print("[NurseFern] Loading page...")
                await page.goto(self.base_url, timeout=120000)
                
                # Wait for page to load
                print("[NurseFern] Waiting for content to load...")
                await asyncio.sleep(10)
                
                # Scroll to load all job cards
                print("[NurseFern] Scrolling to load all jobs...")
                for i in range(15):
                    await page.evaluate("window.scrollBy(0, 600)")
                    await asyncio.sleep(0.5)
                
                # Scroll back to top
                await page.evaluate("window.scrollTo(0, 0)")
                await asyncio.sleep(2)
                
                # Get all job cards using the correct selector
                # Job cards have class: clickable-element bubble-element Group baTaHhaH
                job_cards = await page.query_selector_all('.clickable-element.baTaHhaH')
                print(f"[NurseFern] Found {len(job_cards)} job cards")
                
                # If specific selector doesn't work, try broader selector
                if len(job_cards) == 0:
                    job_cards = await page.query_selector_all('[class*="clickable-element"][class*="baTaH"]')
                    print(f"[NurseFern] Fallback selector found {len(job_cards)} cards")
                
                # Extract job data by clicking each card
                for i, card in enumerate(job_cards):
                    try:
                        print(f"[NurseFern] Processing job {i+1}/{len(job_cards)}...")
                        
                        # Click the card to open detail popup
                        await card.click()
                        await asyncio.sleep(1.5)
                        
                        # Extract data from popup (#job-pop-out)
                        job_data = await page.evaluate('''() => {
                            const popup = document.querySelector('#job-pop-out');
                            if (!popup) return null;
                            
                            // Get job title from h4.baTaIaVo
                            const titleEl = popup.querySelector('h4.baTaIaVo, h4[class*="baTaIaVo"]');
                            const title = titleEl ? titleEl.innerText.trim() : '';
                            
                            // Get company from h5.baTaIaVu
                            const companyEl = popup.querySelector('h5.baTaIaVu, h5[class*="baTaIaVu"]');
                            const company = companyEl ? companyEl.innerText.trim() : '';
                            
                            // Get date from h6.baTaIaVi
                            const dateEl = popup.querySelector('h6.baTaIaVi, h6[class*="baTaIaVi"]');
                            const date = dateEl ? dateEl.innerText.trim() : '';
                            
                            // Get remote status from badge
                            let remoteStatus = 'Remote';
                            const badges = popup.querySelectorAll('h5[class*="baTaMwv"], h5[class*="baTaHiaF"]');
                            badges.forEach(b => {
                                const text = b.innerText.trim().toUpperCase();
                                if (['REMOTE', 'HYBRID', 'ONSITE'].includes(text)) {
                                    remoteStatus = text;
                                }
                            });
                            
                            // Get salary from div.baTaIaf
                            const salaryEl = popup.querySelector('div.baTaIaf, [class*="baTaIaf"]');
                            const salary = salaryEl ? salaryEl.innerText.trim() : '';
                            
                            // Get job type
                            const jobTypeEl = popup.querySelector('div.baTaIaZr, [class*="baTaIaZr"]');
                            const jobType = jobTypeEl ? jobTypeEl.innerText.trim() : '';
                            
                            // Get schedule
                            const scheduleEl = popup.querySelector('div.baTaIaaH, [class*="baTaIaaH"]');
                            const schedule = scheduleEl ? scheduleEl.innerText.trim() : '';
                            
                            // Get license requirements
                            const licenseEl = popup.querySelector('div.baTaIaZaN, [class*="baTaIaZaN"]');
                            const license = licenseEl ? licenseEl.innerText.trim() : '';
                            
                            // Get specialties
                            const specialtyEl = popup.querySelector('div.baTaIbaD, [class*="baTaIbaD"]');
                            const specialties = specialtyEl ? specialtyEl.innerText.trim() : '';
                            
                            // Get job description
                            const descEl = popup.querySelector('div.baTaMbaL, [class*="baTaMbaL"]');
                            const description = descEl ? descEl.innerText.trim().substring(0, 2000) : '';
                            
                            return {
                                title: title,
                                company: company,
                                date: date,
                                remoteStatus: remoteStatus,
                                salary: salary,
                                jobType: jobType,
                                schedule: schedule,
                                license: license,
                                specialties: specialties,
                                description: description
                            };
                        }''')
                        
                        if job_data and job_data.get('title'):
                            self.jobs.append({
                                "job_title": job_data.get("title", ""),
                                "company": job_data.get("company", ""),
                                "date_posted": self._parse_date(job_data.get("date", "")),
                                "location": "Remote",
                                "remote_status": job_data.get("remoteStatus", "Remote"),
                                "employment_type": self._map_job_type(job_data.get("jobType", "")),
                                "schedule": job_data.get("schedule", ""),
                                "license_requirements": job_data.get("license", ""),
                                "salary_range": job_data.get("salary", ""),
                                "job_description": job_data.get("description", ""),
                                "apply_link": self.base_url,
                                "specialties": job_data.get("specialties", ""),
                                "source_site": "NurseFern",
                                "scraped_at": datetime.now().isoformat()
                            })
                        
                        # Close popup by pressing Escape or clicking close button
                        await page.keyboard.press('Escape')
                        await asyncio.sleep(0.5)
                        
                    except Exception as e:
                        print(f"[NurseFern] Error processing job {i+1}: {e}")
                        continue
                
            except Exception as e:
                print(f"[NurseFern] Error: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"[NurseFern] Total jobs scraped: {len(self.jobs)}")
        return self.jobs
    
    def _parse_date(self, date_str: str) -> str:
        if not date_str:
            return datetime.now().strftime("%Y-%m-%d")
        match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{2,4})', date_str)
        if match:
            m, d, y = match.groups()
            if len(y) == 2:
                y = "20" + y
            return f"{y}-{m.zfill(2)}-{d.zfill(2)}"
        return date_str
    
    def _map_job_type(self, job_type: str) -> str:
        if not job_type:
            return "Full-time"
        jt = job_type.upper()
        if "FT" in jt or "FULL" in jt:
            return "Full-time"
        if "PT" in jt or "PART" in jt:
            return "Part-time"
        if "CONTRACT" in jt:
            return "Contract"
        return job_type


async def main():
    scraper = NurseFernScraper()
    jobs = await scraper.scrape(headless=True)
    
    print(f"\n=== Results ===")
    print(f"Total jobs: {len(jobs)}")
    for i, j in enumerate(jobs[:20], 1):
        print(f"{i}. {j['job_title'][:45]} | {j['company'][:18]} | {j['salary_range'][:20]}")


if __name__ == "__main__":
    asyncio.run(main())
