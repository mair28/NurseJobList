"""
Job deduplication module - tracks seen jobs and filters out duplicates.
"""

import os
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Set

# File to store seen job hashes
SEEN_JOBS_FILE = os.path.join(os.path.dirname(__file__), "..", "output", "seen_jobs.json")


def get_job_hash(job: Dict) -> str:
    """Generate a unique hash for a job based on title, company, and apply link."""
    # Use apply_link as primary identifier, fallback to title+company
    key = job.get("apply_link", "")
    if not key:
        key = f"{job.get('job_title', '')}-{job.get('company', '')}"
    
    return hashlib.md5(key.encode()).hexdigest()


def load_seen_jobs() -> Dict:
    """Load the set of previously seen job hashes."""
    if os.path.exists(SEEN_JOBS_FILE):
        try:
            with open(SEEN_JOBS_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"hashes": [], "last_updated": None}


def save_seen_jobs(data: Dict):
    """Save the set of seen job hashes."""
    os.makedirs(os.path.dirname(SEEN_JOBS_FILE), exist_ok=True)
    data["last_updated"] = datetime.now().isoformat()
    with open(SEEN_JOBS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def filter_new_jobs(jobs: List[Dict]) -> List[Dict]:
    """Filter out jobs that have been seen before. Returns only new jobs."""
    seen_data = load_seen_jobs()
    seen_hashes = set(seen_data.get("hashes", []))
    
    new_jobs = []
    new_hashes = []
    
    for job in jobs:
        job_hash = get_job_hash(job)
        if job_hash not in seen_hashes:
            new_jobs.append(job)
            new_hashes.append(job_hash)
            seen_hashes.add(job_hash)
    
    # Update seen jobs file with new hashes
    if new_hashes:
        seen_data["hashes"] = list(seen_hashes)
        save_seen_jobs(seen_data)
    
    print(f"[Dedup] Total scraped: {len(jobs)}, New jobs: {len(new_jobs)}, Already seen: {len(jobs) - len(new_jobs)}")
    
    return new_jobs


def reset_seen_jobs():
    """Reset the seen jobs tracker (useful for testing)."""
    if os.path.exists(SEEN_JOBS_FILE):
        os.remove(SEEN_JOBS_FILE)
        print("[Dedup] Reset seen jobs tracker")
