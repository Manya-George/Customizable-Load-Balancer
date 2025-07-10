import aiohttp
import asyncio
import time
from collections import Counter

URL = "http://localhost:5000/home"
TOTAL_REQUESTS = 1000

async def fetch(session):
    try:
        async with session.get(URL, timeout=5) as resp:

            data = await resp.json()
            return data.get("message", "Unknown")
    except Exception as e:
        return "Error"

async def main():
    print("Sending initial requests to check healthy servers...")
    await asyncio.sleep(10)

    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session) for _ in range(TOTAL_REQUESTS)]
        responses = await asyncio.gather(*tasks)
        counts = Counter(responses)

    print("\n Initial request distribution:")
    for key, val in counts.items():
        print(f"{key}: {val}")

    print("\n Now simulate a server failure (stop server2 container).")
    input("Press Enter to continue after stopping server2...")

    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session) for _ in range(TOTAL_REQUESTS)]
        responses = await asyncio.gather(*tasks)
        counts = Counter(responses)

    print("\n After failure, request distribution:")
    for key, val in counts.items():
        print(f"{key}: {val}")

    print("\n Observe if requests are rerouted (no more Server 2 responses).")

asyncio.run(main())