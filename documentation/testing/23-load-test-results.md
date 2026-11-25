# Load Test Results — Prediqo Backend

**Date:** November 25, 2026
**Environment:** Local development (Windows 11, SQLite, single uvicorn worker)
**Test tool:** `backend/tests/load_test_simple.py` (asyncio + httpx)

## Test Configuration

| Parameter | Value |
|---|---|
| Users | 50 concurrent |
| Duration | 20 seconds |
| Host | http://127.0.0.1:8000 |
| Database | SQLite (single file) |
| Redis | Unavailable (dev mode) |
| Workers | 1 (uvicorn default) |

## Results

| Metric | Value | Target | Status |
|---|---|---|---|
| Total requests | 1,340 | — | — |
| Requests/sec | 64.9 | 500 | ❌ Below target |
| Errors | 0 (0.0%) | < 1% | ✅ Pass |
| Median latency | 593 ms | < 200ms | ❌ Above target |
| p95 latency | 1,672 ms | < 200ms | ❌ Above target |
| p99 latency | 1,797 ms | — | — |
| Max latency | 2,062 ms | — | — |

## Per-Endpoint Breakdown

| Endpoint | Requests | p95 (ms) | Errors |
|---|---|---|---|
| /health | 562 | 766 | 0 |
| /api/v1/fixtures (list) | 267 | 1,797 | 0 |
| /api/v1/fixtures/trending | 153 | 1,406 | 0 |
| /api/v1/predictions | 116 | 453 | 0 |
| /api/v1/performance/overview | 121 | 375 | 0 |
| /api/v1/competitions | 55 | 390 | 0 |
| /api/v1/search | 66 | 485 | 0 |

## Bottlenecks Identified

1. **SQLite single-writer** — File-based DB with no concurrent write support; reads also contend under load
2. **No Redis caching** — Every request hits the database; no caching layer
3. **Synchronous DB calls** — Some endpoints use blocking DB operations
4. **Single worker** — Only one uvicorn process handling all requests
5. **No connection pooling** — SQLite connections are created per-request
6. **No query optimization** — N+1 queries in some endpoints (e.g., list_users refreshes roles per user)

## Recommendations for Production

### Immediate (before launch)
1. **Switch to PostgreSQL** — Multi-connection, concurrent reads/writes, connection pooling
2. **Enable Redis caching** — Cache fixtures, predictions, competitions (TTL: 5 min)
3. **Run multiple uvicorn workers** — `--workers 4` (or use gunicorn)
4. **Add database connection pooling** — SQLAlchemy async pool (pool_size=20, max_overflow=40)

### Short-term (post-launch)
5. **Add response caching headers** — ETag/Last-Modified for GET endpoints
6. **Optimize N+1 queries** — Use joinedload/selectinload for relationships
7. **Add read replicas** — Separate read/write database connections
8. **CDN for static assets** — Cache API responses at edge

### Expected improvements
- PostgreSQL + Redis + 4 workers: **~500-1000 RPS**, p95 < 100ms
- With caching: **~2000+ RPS** for cached endpoints

## Notes

- These results are from **local development** on a Windows PC with SQLite
- Production with PostgreSQL + Redis + multiple workers should be significantly faster
- The 0% error rate is good — no crashes or timeouts under load
- The latency issue is primarily the database, not the application logic