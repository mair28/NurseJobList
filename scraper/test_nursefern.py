"""
Test fetching NurseFern page content.
"""
import httpx
from bs4 import BeautifulSoup

# Fetch the page
print("Fetching NurseFern...")
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

response = httpx.get("https://app.nursefern.com", headers=headers, timeout=30, follow_redirects=True)
print(f"Status: {response.status_code}")
print(f"Content length: {len(response.text)}")

soup = BeautifulSoup(response.text, 'lxml')

# Check for any job-related content
h4s = soup.find_all('h4')
print(f"\nH4 elements: {len(h4s)}")
for h4 in h4s[:10]:
    print(f"  - {h4.get_text(strip=True)[:60]}")

# Check for script tags that might contain job data
scripts = soup.find_all('script')
print(f"\nScript tags: {len(scripts)}")

# Look for any JSON data in scripts
import re
for script in scripts:
    text = script.get_text()
    if 'job' in text.lower() and len(text) > 100:
        print(f"\nFound script with 'job' content ({len(text)} chars)")
        # Look for JSON-like patterns
        if '{' in text and '}' in text:
            print("  Contains JSON-like data")
