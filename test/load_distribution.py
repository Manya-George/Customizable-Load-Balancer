import aiohttp
import asyncio
from collections import Counter
import time
import matplotlib.pyplot as plt

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

    servers = list(counts.keys())
    values = list(counts.values())

    plt.bar(servers, values, color='skyblue')
    plt.xlabel("Servers")
    plt.ylabel("Number of Requests")
    plt.title("Request Distribution Among Servers")
    plt.xticks(rotation=15)
    plt.tight_layout()
    plt.savefig("load_distribution_chart.png")
    print("Chart saved as load_distribution_chart.png")

asyncio.run(main())
