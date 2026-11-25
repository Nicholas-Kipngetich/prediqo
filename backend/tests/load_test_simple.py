"""Simple load test for Prediqo backend API.

No external dependencies required — uses httpx (already installed).

Usage:
    python tests/load_test_simple.py --users 50 --duration 30 --host http://127.0.0.1:8000

Targets (from architecture docs):
  - 500 requests/second
  - 2,000 concurrent users
  - p95 latency < 200ms for reads, < 500ms for writes
"""

import argparse
import asyncio
import random
import statistics
import time

import httpx


ENDPOINTS = [
    ("/health", "GET", 10),
    ("/api/v1/fixtures?page=1&page_size=20&status=SCHEDULED", "GET", 5),
    ("/api/v1/fixtures/trending?page=1&page_size=20", "GET", 3),
    ("/api/v1/predictions?market=1X2", "GET", 2),
    ("/api/v1/performance/overview", "GET", 2),
    ("/api/v1/competitions", "GET", 1),
    ("/api/v1/search?q=Sample&limit=5", "GET", 1),
]


async def worker(client: httpx.AsyncClient, duration: float, results: list):
    end_time = time.monotonic() + duration
    while time.monotonic() < end_time:
        path, method, weight = random.choice(
            [(p, m, w) for p, m, w in ENDPOINTS for _ in range(w)]
        )
        start = time.monotonic()
        try:
            resp = await client.get(path)
            elapsed = (time.monotonic() - start) * 1000
            results.append((path, resp.status_code, elapsed))
        except Exception as exc:
            elapsed = (time.monotonic() - start) * 1000
            results.append((path, 0, elapsed))


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="http://127.0.0.1:8000")
    parser.add_argument("--users", type=int, default=50)
    parser.add_argument("--duration", type=int, default=30)
    args = parser.parse_args()

    print(f"Load test: {args.users} users, {args.duration}s, host={args.host}")
    print(f"Endpoints: {len(ENDPOINTS)}")
    print("-" * 60)

    async with httpx.AsyncClient(base_url=args.host, timeout=10.0) as client:
        results: list = []
        tasks = [asyncio.create_task(worker(client, args.duration, results)) for _ in range(args.users)]
        start = time.monotonic()
        await asyncio.gather(*tasks)
        total_time = time.monotonic() - start

    # Analyze results
    total = len(results)
    errors = sum(1 for _, status, _ in results if status == 0 or status >= 400)
    rps = total / total_time
    latencies = [elapsed for _, _, elapsed in results]
    latencies.sort()

    print(f"\nResults:")
    print(f"  Total requests:  {total}")
    print(f"  Total time:      {total_time:.1f}s")
    print(f"  Requests/sec:    {rps:.1f}")
    print(f"  Errors:          {errors} ({errors/total*100:.1f}%)")
    print(f"  Latency (ms):")
    print(f"    min:    {min(latencies):.1f}")
    print(f"    median: {statistics.median(latencies):.1f}")
    print(f"    p95:    {latencies[int(len(latencies)*0.95)]:.1f}")
    print(f"    p99:    {latencies[int(len(latencies)*0.99)]:.1f}")
    print(f"    max:    {max(latencies):.1f}")

    # Per-endpoint breakdown
    print("\nPer-endpoint:")
    for path, _, _ in ENDPOINTS:
        ep_results = [(s, e) for p, s, e in results if p == path]
        if ep_results:
            ep_latencies = sorted(e for _, e in ep_results)
            ep_errors = sum(1 for s, _ in ep_results if s == 0 or s >= 400)
            print(f"  {path[:50]:50s} reqs={len(ep_results):4d} p95={ep_latencies[int(len(ep_latencies)*0.95)]:6.1f}ms errors={ep_errors}")


if __name__ == "__main__":
    asyncio.run(main())