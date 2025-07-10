import aiohttp
import asyncio
from collections import Counter
import time

URL = "http://localhost:5000/home"
TOTAL_REQUESTS = 10000
MAX_CONCURRENT = 100  # limit concurrent requests

semaphore = asyncio.Semaphore(MAX_CONCURRENT)

async def fetch(session):
    async with semaphore:
        try:
            async with session.get(URL, timeout=10) as resp:
                data = await resp.json()
                return data.get("message", "Unknown")
        except:
            return "Error"

async def main():
    print("Waiting 10 seconds for services to be ready...")
    time.sleep(10)

    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session) for _ in range(TOTAL_REQUESTS)]
        responses = await asyncio.gather(*tasks)
        counts = Counter(responses)

        print(f"A-1: Request Distribution among 3 servers (Total: {TOTAL_REQUESTS})")
        for server, count in sorted(counts.items()):
            print(f"{server}: {count} requests")

asyncio.run(main())