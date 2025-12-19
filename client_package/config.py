"""
Configuration for HealthGigHub Job Scraper
==========================================

SETUP INSTRUCTIONS:
1. Get a rotating proxy from a provider like:
   - Webshare.io (recommended)
   - Bright Data
   - Smartproxy
   
2. Replace the PROXY_URL below with your proxy credentials

3. Run the scraper: python requests_scraper.py
"""

import os
from datetime import datetime

# =============================================================================
# PROXY CONFIGURATION (REQUIRED)
# =============================================================================
# Format: http://username:password@host:port
# Example: http://myuser-rotate:mypass123@p.webshare.io:80
#
# Get a rotating proxy from: https://www.webshare.io/ (recommended)
# =============================================================================

PROXY_URL = os.environ.get("PROXY_URL", "http://YOUR_USERNAME:YOUR_PASSWORD@YOUR_PROXY_HOST:PORT")

# If you don't have a proxy, you can try without one (may get blocked):
# PROXY_URL = None


# =============================================================================
# OPTIONAL SETTINGS (defaults work fine)
# =============================================================================

# Maximum jobs to scrape per site (0 = unlimited)
MAX_JOBS_PER_SITE = 100

# Output directory
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")

# Target URLs
URLS = {
    "remotenurse": "https://remotenurseconnection.com/remote-nursing-job-board/",
    "nursefern": "https://app.nursefern.com/",
}

# Output columns for CSV
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


def get_output_filename(extension: str = "csv") -> str:
    """Generate output filename with today's date."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return os.path.join(OUTPUT_DIR, f"jobs_{date_str}.{extension}")
