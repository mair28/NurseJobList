# HealthGigHub Job Scraper

Automated scraper for pulling RN job listings from external job boards and exporting them in a format ready for WordPress upload.

## Features

- ✅ **Scrapes 2 job boards:**
  - Remote Nurse Connection (remotenurseconnection.com)
  - NurseFern (app.nursefern.com)
- ✅ **Extracts key fields:** job title, company, job type, location, pay, description, apply link, date posted
- ✅ **Standardized output** matching HealthGigHub format
- ✅ **Clean CSV export** for VA to upload to WordPress
- ✅ **Daily scheduling** support
- ✅ **No browser required** - fast, lightweight requests-based scraping

## Installation

```bash
cd scraper
pip install -r requirements.txt
```

## Usage

### Run Once (Manual)

```bash
python requests_scraper.py
```

Output will be saved to `output/jobs_YYYY-MM-DD.csv`

### Run on Schedule (Daily)

```bash
python requests_scraper.py --schedule 09:00
```

This will:
1. Run immediately on start
2. Then run every day at 9:00 AM
3. Keep running until stopped (Ctrl+C)

### Run with Windows Task Scheduler

For production, set up Windows Task Scheduler to run the scraper daily:

1. Open Task Scheduler
2. Create Basic Task → Name: "HealthGigHub Scraper"
3. Trigger: Daily at your preferred time
4. Action: Start a program
   - Program: `python`
   - Arguments: `C:\path\to\scraper\requests_scraper.py`
   - Start in: `C:\path\to\scraper`

## Output Format

The CSV output includes these columns:

| Field | Description |
|-------|-------------|
| job_title | Position title |
| company | Hiring company name |
| date_posted | When the job was posted |
| location | Job location or remote states |
| remote_status | Remote, Hybrid, or On-site |
| employment_type | Full-time, Part-time, Contract, etc. |
| schedule | Work schedule (Full-time, Days, etc.) |
| license_requirements | Required licenses/certifications |
| salary_range | Pay range if available |
| job_description | Full job description |
| apply_link | Direct apply URL |
| specialties | Nursing specialties |
| source_site | Which job board it came from |
| scraped_at | Timestamp of scrape |

## Configuration

Edit `config.py` to customize:

- `MAX_JOBS_PER_SITE` - Limit jobs per source (default: 100)
- `PROXY_URL` - Rotating proxy for Cloudflare bypass
- `CAPSOLVER_API_KEY` - For CAPTCHA solving (if needed)

## File Structure

```
healthgighub/
├── scraper/
│   ├── requests_scraper.py  # Main scraper (RECOMMENDED)
│   ├── main.py              # Browser-based scraper (backup)
│   ├── config.py            # Settings and API keys
│   ├── formatter.py         # Output formatting
│   ├── remotenurse.py       # Remote Nurse Connection module
│   ├── nursefern.py         # NurseFern module
│   └── browser.py           # Browser automation (backup)
├── output/
│   └── jobs_YYYY-MM-DD.csv  # Daily output files
└── README.md
```

## Technical Notes

### Remote Nurse Connection
- Uses cloudscraper + rotating proxy to bypass Cloudflare
- Parses job pages for all fields

### NurseFern
- Direct API access at `/api/1.1/obj/job`
- Filters out archived/deleted jobs
- Extracts company from job link URL

## Troubleshooting

**Cloudflare blocking?**
- The rotating proxy should handle this automatically
- If still blocked, wait 5-10 minutes and try again
- Check if proxy credentials are valid in `config.py`

**No jobs from NurseFern?**
- Most jobs may be archived on their platform
- Check their website manually to verify active listings

**Empty fields?**
- Some fields are only available on certain jobs
- Pay/salary is not always listed by employers
