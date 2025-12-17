## Project Overview

This proposal outlines the development of an automated web scraping solution to collect, standardize, and export RN job listings from two external job boards for integration into HealthGigHub.com.

---

## Scope of Work

### Target Job Boards

- Remote Nurse Connection: https://remotenurseconnection.com/remote-nursing-job-board/
- NurseFern: https://app.nursefern.com/

### Data Fields to Extract

Based on my preliminary analysis of both job boards, the following fields are available and will be extracted:

| Field | Remote Nurse Connection | NurseFern |
|-------|------------------------|-----------|
| Job Title | Available | Available |
| Company Name | Available | Available |
| Date Posted | Available | Available |
| Location | Available | Available |
| Remote Status | Available (Hybrid/Remote/On-site) | Available (Remote tags) |
| Employment Type | Available (Full-time/Part-time/Contract) | Available (FT/PT) |
| Schedule | Available | Available |
| License Requirements | Available (State codes) | Available (RN + State requirements) |
| Salary/Pay Range | Not always listed | Available when disclosed |
| Job Description | Full text available | Full text available |
| Apply Link | Direct company link | Available |
| Specialties/Categories | Available | Available |

### Deliverables

1. Python-based web scraper covering both job boards
2. Anti-bot bypass implementation for reliable automated access
3. Data standardization module to match HealthGigHub's job format
4. Scheduling capability for daily or custom execution
5. Clean CSV output for easy WordPress import
6. Documentation with setup instructions and usage guide

---

## Technical Approach

**Remote Nurse Connection:**
- WordPress-based site with Cloudflare protection
- Job listings open in new tabs with consistent page structure
- Will implement stealth browser automation to bypass anti-bot measures

**NurseFern:**
- Built on Bubble.io with dynamic JavaScript rendering
- Job details appear in modal popups
- Will use browser automation with anti-detection measures

Both scrapers will include error handling, logging, retry mechanisms, and session management to ensure reliable daily operation.

---

## Project Timeline

| Phase | Task | Estimated Hours |
|-------|------|-----------------|
| 1 | Research and analysis of both job board structures | 1-2 hrs |
| 2 | Anti-bot bypass implementation and testing | 2-3 hrs |
| 3 | Develop scraper for Remote Nurse Connection | 3-4 hrs |
| 4 | Develop scraper for NurseFern | 3-4 hrs |
| 5 | Data formatting and standardization | 1-1.5 hrs |
| 6 | Testing, debugging, and documentation | 1.5-2 hrs |

**Total Estimated Time:** 12-15 hours

---

## Ongoing Support (Optional)

After the initial build, I am available for ongoing maintenance at the same hourly rate. This includes minor fixes, updates if site structures change, or adding additional job board sources as your needs grow.

---

## Requirements from Your End

To proceed, I will need:

1. Confirmation of this proposal
2. Any login credentials if required for the target sites
3. Sample of your preferred output format or a reference job listing from HealthGigHub
4. Your preferred method for receiving output files (email, Google Drive, etc.)

---

## Next Steps

1. You confirm this proposal and send the deposit via Wise
2. I begin research and development
3. Progress updates provided throughout
4. Delivery and review

