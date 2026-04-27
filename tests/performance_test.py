# tests/performance_test.py
# FINAL STABLE PERFORMANCE TEST
# Target: 50 Requests | 0 Failures | 15-25 sec realistic

import asyncio
import time
import httpx

URL = "http://localhost:8000/career-search"

TOTAL_REQUESTS = 50
MAX_WORKERS = 8

PAYLOAD = {
    "question": "what is doctor?"
}

# =====================================================
sem = asyncio.Semaphore(MAX_WORKERS)

# =====================================================
async def send_request(client, i):

    async with sem:

        start = time.perf_counter()

        try:
            r = await client.post(
                URL,
                data=PAYLOAD
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

    limits = httpx.Limits(
        max_keepalive_connections=30,
        max_connections=50
    )

    timeout = httpx.Timeout(
        connect=10,
        read=120,
        write=30,
        pool=30
    )

    async with httpx.AsyncClient(
        limits=limits,
        timeout=timeout
    ) as client:

        tasks = [
            send_request(client, i + 1)
            for i in range(TOTAL_REQUESTS)
        ]

        results = await asyncio.gather(*tasks)

    total_end = time.perf_counter()

    # =================================================
    success = [x for x in results if x["ok"]]
    failed = [x for x in results if not x["ok"]]

    times = [x["time"] for x in success]

    avg = round(sum(times)/len(times),2) if times else 0
    mn = round(min(times),2) if times else 0
    mx = round(max(times),2) if times else 0

    total = round(total_end-total_start,2)

    rps = round(TOTAL_REQUESTS/total,2) if total else 0

    success_rate = round(
        len(success)/TOTAL_REQUESTS*100,2
    )

    # =================================================
    print("========== RESULT ==========")
    print("Total Requests :", TOTAL_REQUESTS)
    print("Parallel Users :", MAX_WORKERS)
    print("Success        :", len(success))
    print("Failed         :", len(failed))
    print("Success Rate   :", success_rate, "%")
    print("Average Time   :", avg, "sec")
    print("Min Time       :", mn, "sec")
    print("Max Time       :", mx, "sec")
    print("Requests/Sec   :", rps)
    print("Total Test Time:", total, "sec")

    if failed:
        print("\nFailed Requests:")
        for f in failed[:10]:
            print(f)

    print("\nDone.")

# =====================================================
if __name__ == "__main__":
    asyncio.run(main())