"""Load test for Prediqo backend API.

Run with: locust -f tests/load_test.py --host http://127.0.0.1:8000
Or:       locust -f tests/load_test.py --host http://127.0.0.1:8000 --headless -u 50 -r 5 -t 60s

Targets (from architecture docs):
  - 500 requests/second
  - 2,000 concurrent users
  - p95 latency < 200ms for reads, < 500ms for writes
"""

from locust import HttpUser, between, task


class PrediqoUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # Health check to warm up
        self.client.get("/health")

    @task(10)
    def health_check(self):
        self.client.get("/health")

    @task(5)
    def list_fixtures(self):
        self.client.get("/api/v1/fixtures?page=1&page_size=20&status=SCHEDULED")

    @task(3)
    def list_trending(self):
        self.client.get("/api/v1/fixtures/trending?page=1&page_size=20")

    @task(2)
    def list_predictions(self):
        self.client.get("/api/v1/predictions?market=1X2")

    @task(2)
    def performance_overview(self):
        self.client.get("/api/v1/performance/overview")

    @task(1)
    def list_competitions(self):
        self.client.get("/api/v1/competitions")

    @task(1)
    def token_balance(self):
        # Requires auth; will return 401 but tests endpoint availability
        self.client.get("/api/v1/tokens/balance")

    @task(1)
    def search(self):
        self.client.get("/api/v1/search?q=Sample&limit=5")