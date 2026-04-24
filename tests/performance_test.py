# tests/performance_test.py
# FAST PERFORMANCE TEST
# 10 Concurrent Requests

import asyncio
import time
import httpx

URL = "http://localhost:8000/career-search"
TOTAL_REQUESTS = 50

PAYLOAD = {
    "question": "what is doctor?"
}

# limit active parallel workers
MAX_WORKERS = 5


# =====================================================
sem = asyncio.Semaphore(MAX_WORKERS)


async def send_request(client, i):

    async with sem:

        start = time.perf_counter()

        try:
            r = await client.post(
                URL,
                data=PAYLOAD,
                timeout=90
            )

            end = time.perf_counter()

            return {
                "id": i,
                "ok": r.status_code == 200,
                "status": r.status_code,
                "time": round(end - start, 2)
            }

        except Exception as e:

            end = time.perf_counter()

            return {
                "id": i,
                "ok": False,
                "status": "ERROR",
                "time": round(end - start, 2),
                "error": str(e)
            }


# =====================================================
async def main():

    print(f"\nStarting {TOTAL_REQUESTS} requests...")
    print(f"Parallel Workers: {MAX_WORKERS}\n")

    total_start = time.perf_counter()

    async with httpx.AsyncClient() as client:

        tasks = [
            send_request(client, i + 1)
            for i in range(TOTAL_REQUESTS)
        ]

        results = await asyncio.gather(*tasks)

    total_end = time.perf_counter()

    # -----------------------------------------
    success = [x for x in results if x["ok"]]
    failed = [x for x in results if not x["ok"]]

    times = [x["time"] for x in success]

    avg = round(sum(times)/len(times),2) if times else 0
    mn = round(min(times),2) if times else 0
    mx = round(max(times),2) if times else 0

    # -----------------------------------------
    print("========== RESULT ==========")
    print("Total Requests :", TOTAL_REQUESTS)
    print("Success        :", len(success))
    print("Failed         :", len(failed))
    print("Average Time   :", avg, "sec")
    print("Min Time       :", mn, "sec")
    print("Max Time       :", mx, "sec")
    print("Total Test Time:", round(total_end-total_start,2), "sec")

    if failed:
        print("\nFailed:")
        for f in failed:
            print(f)

    print("\nDone.")


# =====================================================
if __name__ == "__main__":
    asyncio.run(main())