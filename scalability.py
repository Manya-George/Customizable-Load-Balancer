import aiohttp
import asyncio
from collections import Counter
import time

TOTAL_REQUESTS = 10000
MAX_CONCURRENT = 100
SERVER_IDS = [f"Hello from Server: {i}" for i in range(1, 7)]
URL = "http://localhost:5000/home"

semaphore = asyncio.Semaphore(MAX_CONCURRENT)

async def fetch(session):
    async with semaphore:
        try:
            async with session.get(URL, timeout=10) as resp:
                data = await resp.json()
                return data.get("message", "Unknown")
        except:
            return "Error"

async def test_n_servers(n):
    print(f"\nTesting with N={n} servers...")
    # Simulate delay if containers were just added
    await asyncio.sleep(3)

    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session) for _ in range(TOTAL_REQUESTS)]
        responses = await asyncio.gather(*tasks)
        counts = Counter(responses)

        total_handled = 0
        print(f"--- Result for N={n} ---")
        for sid in SERVER_IDS[:n]:
            handled = counts.get(sid, 0)
            total_handled += handled
            print(f"{sid}: {handled} requests")

        errors = counts.get("Error", 0)
        print(f"Errors: {errors}")
        print(f"Average per server: {total_handled // n} requests\n")

async def main():
    print("Waiting 10 seconds for services to be ready...")
    time.sleep(10)

    for n in range(2, 7):  # From 2 to 6
        await test_n_servers(n)

asyncio.run(main())