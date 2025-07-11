import aiohttp
import asyncio
import time
from collections import Counter
import matplotlib.pyplot as plt

URL = "http://localhost:5000/home"
TOTAL_REQUESTS = 1000

async def fetch(session):
    try:
        async with session.get(URL, timeout=5) as resp:

            data = await resp.json()
            return data.get("message", "Unknown")
    except Exception as e:
        return "Error"

def plot_bar(data, title):
    servers = list(data.keys())
    counts = list(data.values())

    plt.figure(figsize=(8, 4))
    plt.bar(servers, counts, color='salmon')
    plt.title(title)
    plt.xlabel("Server")
    plt.ylabel("Requests")
    plt.xticks(rotation=15)
    plt.tight_layout()
    plt.savefig("fault_tolerance_chart.png")

async def main():
    print("Sending initial requests to check healthy servers...")
    await asyncio.sleep(10)

    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session) for _ in range(TOTAL_REQUESTS)]
        responses = await asyncio.gather(*tasks)
        before_counts = Counter(responses)

    print("\n Initial request distribution:")
    for key, val in before_counts.items():
        print(f"{key}: {val}")

    plot_bar(before_counts, "Request Distribution Before Failure")

    print("\n Now simulate a server failure (stop server2 container).")
    input("Press Enter to continue after stopping server2...")

    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session) for _ in range(TOTAL_REQUESTS)]
        responses = await asyncio.gather(*tasks)
        after_counts = Counter(responses)

    print("\n After failure, request distribution:")
    for key, val in after_counts.items():
        print(f"{key}: {val}")

    plot_bar(after_counts, "Request Distribution After Server2 Failure")

asyncio.run(main())
