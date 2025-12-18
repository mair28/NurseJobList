"""
Configuration settings for the HealthGigHub job scraper.
"""

import os
from datetime import datetime

# Output settings
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")
OUTPUT_FORMAT = "csv"  # csv or json

# Browser settings
HEADLESS = True  # Set to False for debugging
SLOW_MO = 100  # Milliseconds between actions (helps avoid detection)
TIMEOUT = 60000  # Page load timeout in milliseconds

# Scraping settings
MAX_JOBS_PER_SITE = 100  # Maximum jobs to scrape per run (0 = unlimited)
RETRY_ATTEMPTS = 3
RETRY_DELAY = 5  # Seconds between retries

# Target URLs
URLS = {
    "nursefern": "https://app.nursefern.com/",
    "remotenurse": "https://remotenurseconnection.com/remote-nursing-job-board/"
}

# Rotating proxy configuration (can be overridden via environment variable)
PROXY_URL = os.environ.get("PROXY_URL", "http://hiqjuwfu-rotate:xmq4ru7a995q@p.webshare.io:80")

# CSS Selectors for Remote Nurse Connection
REMOTENURSE_SELECTORS = {
    "job_card": ".job_listing",
    "job_link": "a.job_listing-clickbox",
    "job_title": "h1.entry-title",
    "date_posted": ".published",
    "company": ".dp-company-info h4",
    "location": ".et_pb_text_inner",
    "employment_type": ".et_pb_code_inner span",
    "remote_status": ".et_pb_code_inner span",
    "description": ".et_pb_post_content",
    "apply_link": ".dp-additional-link a",
    "categories": ".et_pb_code_inner span"
}

# CSS Selectors for NurseFern
NURSEFERN_SELECTORS = {
    "job_card": ".bubble-element.Group[id*='job']",
    "job_title": "h4",
    "company": "h5",
    "date_posted": "h6",
    "remote_tag": "[style*='background-color: rgb(26, 55, 216)']",
    "location": "[class*='Text']:has-text('MUST WORK FROM')",
    "salary_range": "[class*='Text']:has-text('SALARY RANGE')",
    "job_type": "[class*='Text']:has-text('JOB TYPE')",
    "description": "[class*='Text'][style*='line-height: 1.4']",
    "apply_button": "button:has-text('Apply')"
}

# Output CSV columns (matches HealthGigHub format)
OUTPUT_COLUMNS = [
    "job_title",
    "company",
    "date_posted",
    "location",
    "remote_status",
    "employment_type",
    "schedule",
    "license_requirements",
    "salary_range",
    "job_description",
    "apply_link",
    "specialties",
    "source_site",
    "scraped_at"
]


def get_output_filename():
    """Generate output filename with current date."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(OUTPUT_DIR, f"jobs_{date_str}.csv")
