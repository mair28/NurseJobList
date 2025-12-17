"""
HealthGigHub Job Scraper - Main Entry Point

Scrapes job listings from Remote Nurse Connection and NurseFern,
formats them to match HealthGigHub's format, and exports to CSV.

Usage:
    python main.py              # Run scraper once
    python main.py --schedule   # Run on daily schedule
    python main.py --site nursefern  # Scrape only NurseFern
    python main.py --site remotenurse  # Scrape only Remote Nurse Connection
    python main.py --setup      # Setup Cloudflare session manually
    python main.py --visible    # Run with visible browser (for debugging)
"""

import asyncio
import argparse
import schedule
import time
from datetime import datetime

from browser import StealthBrowser, setup_cloudflare_session
from remotenurse import RemoteNurseScraper
from nursefern import NurseFernScraper
from formatter import JobFormatter
from config import OUTPUT_DIR, URLS


async def run_scraper(sites: list = None, headless: bool = True):
    """Run the scraper for specified sites."""
    print("\n" + "="*60)
    print(f"HealthGigHub Job Scraper - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    if sites is None:
        sites = ["remotenurse", "nursefern"]
    
    # Initialize browser
    browser = StealthBrowser(headless=headless)
    await browser.start()
    
    # Initialize formatter
    formatter = JobFormatter()
    
    try:
        # Scrape each site
        if "remotenurse" in sites:
            scraper = RemoteNurseScraper(browser)
            jobs = await scraper.scrape()
            formatter.add_jobs(jobs)
        
        if "nursefern" in sites:
            scraper = NurseFernScraper(browser)
            jobs = await scraper.scrape()
            formatter.add_jobs(jobs)
        
        # Export results
        if formatter.jobs:
            csv_file = formatter.export_csv()
            
            # Print summary
            summary = formatter.get_summary()
            print("\n" + "="*60)
            print("SCRAPING COMPLETE")
            print("="*60)
            print(f"Total jobs scraped: {summary['total_jobs']}")
            print(f"By source: {summary['by_source']}")
            print(f"Output file: {csv_file}")
        else:
            print("\n[Main] No jobs were scraped")
        
    except Exception as e:
        print(f"\n[Main] Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await browser.close()


def scheduled_job(sites, headless):
    """Wrapper for scheduled runs."""
    asyncio.run(run_scraper(sites, headless))


def main():
    """Main entry point with CLI argument handling."""
    parser = argparse.ArgumentParser(description="HealthGigHub Job Scraper")
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Run on daily schedule (default: 6:00 AM)"
    )
    parser.add_argument(
        "--time",
        type=str,
        default="06:00",
        help="Time to run scheduled job (HH:MM format, default: 06:00)"
    )
    parser.add_argument(
        "--site",
        type=str,
        choices=["remotenurse", "nursefern", "all"],
        default="all",
        help="Which site to scrape (default: all)"
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Open browser to manually solve Cloudflare challenge and save session"
    )
    parser.add_argument(
        "--visible",
        action="store_true",
        help="Run with visible browser window (for debugging)"
    )
    
    args = parser.parse_args()
    
    # Setup mode - manually solve Cloudflare
    if args.setup:
        print("Setting up Cloudflare session for Remote Nurse Connection...")
        asyncio.run(setup_cloudflare_session(URLS["remotenurse"]))
        return
    
    # Determine which sites to scrape
    if args.site == "all":
        sites = ["remotenurse", "nursefern"]
    else:
        sites = [args.site]
    
    # Determine headless mode
    headless = not args.visible
    
    if args.schedule:
        # Run on schedule
        print(f"Scheduling daily scrape at {args.time}")
        print(f"Sites: {', '.join(sites)}")
        print("Press Ctrl+C to stop\n")
        
        schedule.every().day.at(args.time).do(
            lambda: scheduled_job(sites, headless)
        )
        
        # Run immediately on start
        asyncio.run(run_scraper(sites, headless))
        
        # Then wait for scheduled runs
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        # Run once
        asyncio.run(run_scraper(sites, headless))


if __name__ == "__main__":
    main()
