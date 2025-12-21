import httpx
import asyncio

async def check_nursefern():
    r = await httpx.AsyncClient().get('https://app.nursefern.com/api/1.1/obj/job', timeout=15)
    d = r.json()
    results = d.get('response', {}).get('results', [])
    active = [j for j in results if j.get('Internal Job Status') not in ['Archived','Deleted'] and j.get('last_checked_status') != 403]
    
    print(f'API Status: {r.status_code}')
    print(f'Total jobs in API: {len(results)}')
    print(f'Active jobs: {len(active)}')
    print('Active job titles:')
    for j in active:
        print(f"  - {j.get('Job Title')}")

asyncio.run(check_nursefern())
