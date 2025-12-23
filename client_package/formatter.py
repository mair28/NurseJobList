"""
Data formatter to standardize job data for HealthGigHub.
"""

import os
import csv
import json
from datetime import datetime
from typing import List, Dict
from dateutil import parser as date_parser

from config import OUTPUT_DIR, OUTPUT_COLUMNS, get_output_filename


class JobFormatter:
    """Formats and exports scraped job data."""
    
    def __init__(self):
        self.jobs: List[Dict] = []
        
        # Ensure output directory exists
        os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    def add_jobs(self, jobs: List[Dict]):
        """Add jobs to the formatter."""
        self.jobs.extend(jobs)
    
    def format_all(self) -> List[Dict]:
        """Format all jobs to match HealthGigHub's expected format."""
        formatted = []
        
        for job in self.jobs:
            formatted_job = self._format_job(job)
            formatted.append(formatted_job)
        
        # Sort by date_posted descending (latest first/top, oldest last/bottom)
        formatted.sort(key=lambda x: self._parse_date_for_sort(x.get("date_posted", "")), reverse=True)
        
        return formatted
    
    def _parse_date_for_sort(self, date_str: str) -> datetime:
        """Parse date string for sorting. Returns min date if parsing fails."""
        if not date_str:
            return datetime.min
        try:
            return date_parser.parse(date_str, fuzzy=True)
        except:
            return datetime.min
    
    def _format_job(self, job: Dict) -> Dict:
        """Format a single job entry."""
        return {
            "job_title": self._clean_text(job.get("job_title", "")),
            "company": self._clean_text(job.get("company", "")),
            "date_posted": self._format_date(job.get("date_posted", "")),
            "location": self._clean_text(job.get("location", "")),
            "remote_status": self._normalize_remote_status(job.get("remote_status", "")),
            "employment_type": self._normalize_employment_type(job.get("employment_type", "")),
            "schedule": self._clean_text(job.get("schedule", "")),
            "license_requirements": self._clean_text(job.get("license_requirements", "")),
            "salary_range": self._clean_text(job.get("salary_range", "")),
            "job_description": self._clean_description(job.get("job_description", "")),
            "apply_link": job.get("apply_link", ""),
            "specialties": self._clean_text(job.get("specialties", "")),
            "source_site": job.get("source_site", ""),
            "scraped_at": job.get("scraped_at", datetime.now().isoformat())
        }
    
    def _clean_text(self, text: str) -> str:
        """Clean up text content."""
        if not text:
            return ""
        
        # Decode HTML entities
        import html
        text = html.unescape(text)
        
        # Remove HTML tags
        import re
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove excessive whitespace
        text = " ".join(text.split())
        
        # Remove common artifacts
        text = text.replace("\xa0", " ")  # Non-breaking space
        text = text.replace("\u200b", "")  # Zero-width space
        
        return text.strip()
    
    def _clean_description(self, text: str) -> str:
        """Clean job description text for CSV compatibility."""
        if not text:
            return ""
        
        import html
        import re
        
        # Decode HTML entities
        text = html.unescape(text)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # Replace newlines with spaces for CSV compatibility
        text = text.replace('\n', ' ').replace('\r', ' ')
        
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Limit length
        if len(text) > 5000:
            text = text[:5000] + "..."
        
        return text.strip()
    
    def _format_date(self, date_str: str) -> str:
        """Parse and format date to consistent format."""
        if not date_str:
            return ""
        
        try:
            # Try parsing various date formats
            parsed = date_parser.parse(date_str, fuzzy=True)
            return parsed.strftime("%Y-%m-%d")
        except:
            # Return original if parsing fails
            return date_str
    
    def _normalize_remote_status(self, status: str) -> str:
        """Normalize remote status to consistent values."""
        if not status:
            return ""
        
        status_lower = status.lower()
        
        if "remote" in status_lower and "hybrid" not in status_lower:
            return "Remote"
        elif "hybrid" in status_lower:
            return "Hybrid"
        elif "on-site" in status_lower or "onsite" in status_lower:
            return "On-site"
        else:
            return status
    
    def _normalize_employment_type(self, emp_type: str) -> str:
        """Normalize employment type to consistent values."""
        if not emp_type:
            return ""
        
        emp_lower = emp_type.lower()
        
        if "full" in emp_lower or "ft" in emp_lower:
            return "Full-time"
        elif "part" in emp_lower or "pt" in emp_lower:
            return "Part-time"
        elif "contract" in emp_lower:
            return "Contract"
        elif "prn" in emp_lower or "per diem" in emp_lower:
            return "PRN/Per Diem"
        elif "temp" in emp_lower:
            return "Temporary"
        else:
            return emp_type
    
    def export_csv(self, filename: str = None) -> str:
        """Export formatted jobs to CSV file."""
        if not filename:
            filename = get_output_filename()
        
        formatted_jobs = self.format_all()
        
        if not formatted_jobs:
            print("[Formatter] No jobs to export")
            return ""
        
        # Use utf-8-sig for Excel compatibility (includes BOM)
        with open(filename, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
            writer.writeheader()
            
            for job in formatted_jobs:
                # Only write columns defined in OUTPUT_COLUMNS
                row = {}
                for col in OUTPUT_COLUMNS:
                    val = job.get(col, "")
                    # Clean any problematic characters
                    if isinstance(val, str):
                        val = self._clean_for_csv(val)
                    row[col] = val
                writer.writerow(row)
        
        print(f"[Formatter] Exported {len(formatted_jobs)} jobs to {filename}")
        return filename
    
    def _clean_for_csv(self, text: str) -> str:
        """Clean text for CSV compatibility."""
        if not text:
            return ""
        # Replace problematic characters
        text = text.replace('\u2013', '-')  # en-dash
        text = text.replace('\u2014', '-')  # em-dash
        text = text.replace('\u2018', "'")  # left single quote
        text = text.replace('\u2019', "'")  # right single quote
        text = text.replace('\u201c', '"')  # left double quote
        text = text.replace('\u201d', '"')  # right double quote
        text = text.replace('\u2022', '*')  # bullet
        text = text.replace('\u00a0', ' ')  # non-breaking space
        text = text.replace('\r\n', ' ').replace('\r', ' ').replace('\n', ' ')
        # Remove any remaining non-ASCII that might cause issues
        text = text.encode('ascii', 'ignore').decode('ascii')
        return text.strip()
    
    def export_json(self, filename: str = None) -> str:
        """Export formatted jobs to JSON file."""
        if not filename:
            filename = get_output_filename().replace(".csv", ".json")
        
        formatted_jobs = self.format_all()
        
        if not formatted_jobs:
            print("[Formatter] No jobs to export")
            return ""
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(formatted_jobs, f, indent=2, ensure_ascii=False)
        
        print(f"[Formatter] Exported {len(formatted_jobs)} jobs to {filename}")
        return filename
    
    def get_summary(self) -> Dict:
        """Get summary statistics of scraped jobs."""
        formatted_jobs = self.format_all()
        
        sources = {}
        for job in formatted_jobs:
            source = job.get("source_site", "Unknown")
            sources[source] = sources.get(source, 0) + 1
        
        return {
            "total_jobs": len(formatted_jobs),
            "by_source": sources,
            "export_date": datetime.now().isoformat()
        }
