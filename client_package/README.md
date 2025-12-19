# HealthGigHub Job Scraper - Client Setup Guide

## Quick Start

### 1. Install Python
Download and install Python 3.10+ from https://python.org

### 2. Install Dependencies
```bash
cd client_package
pip install -r requirements.txt
```

### 3. Configure Your Proxy (REQUIRED)

Edit `config.py` and replace the proxy placeholder with your credentials:

```python
PROXY_URL = "http://YOUR_USERNAME:YOUR_PASSWORD@YOUR_PROXY_HOST:PORT"
```

**Example with Webshare.io proxy:**
```python
PROXY_URL = "http://myuser-rotate:mypass123@p.webshare.io:80"
```

> ⚠️ **A rotating proxy is required** to bypass Cloudflare protection.
> Recommended provider: [Webshare.io](https://www.webshare.io/) ($5/month for unlimited)

### 4. Run the Scraper
```bash
python requests_scraper.py
```

Output files will be saved to the `output/` folder:
- `jobs_YYYY-MM-DD.csv` - CSV format for Excel/Google Sheets
- `jobs_YYYY-MM-DD.json` - JSON format for automation

---

## Scheduling (Optional)

### Run Every 4 Hours
```bash
python requests_scraper.py --schedule 09:00
```

### Windows Task Scheduler
1. Open Task Scheduler
2. Create Basic Task → "HealthGigHub Scraper"
3. Trigger: Daily at preferred time
4. Action: Start a program
   - Program: `python`
   - Arguments: `C:\path\to\client_package\requests_scraper.py`

---

## Files Included

| File | Description |
|------|-------------|
| `requests_scraper.py` | Main scraper script |
| `config.py` | Configuration (edit your proxy here) |
| `formatter.py` | Data formatting and CSV export |
| `dedup.py` | Deduplication (only saves new jobs) |
| `requirements.txt` | Python dependencies |

---

## Output Format

The CSV contains these columns:
- job_title
- company
- date_posted
- location
- remote_status
- employment_type
- schedule
- license_requirements
- salary_range
- job_description
- apply_link
- specialties
- source_site
- scraped_at

---

## Troubleshooting

**"403 Forbidden" or Cloudflare blocking?**
- Make sure your proxy is configured correctly
- Ensure you're using a rotating residential proxy

**No new jobs found?**
- The scraper tracks previously seen jobs
- Delete `output/seen_jobs.json` to reset and rescrape all jobs

**Import errors?**
- Run `pip install -r requirements.txt` again

---

## Support

For issues or questions, contact: [your email here]
