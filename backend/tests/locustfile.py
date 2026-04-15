from locust import HttpUser, task, between

class SearchUser(HttpUser):
    wait_time = between(1, 3)   # each user waits 1-3s between requests

    @task(3)
    def search_cached(self):
        """High-frequency cached query — should be very fast."""
        self.client.get(
            "/api/search",
            params={"q": "Who directed Inception?"},
            name="/api/search [cached]"
        )

    @task(1)
    def search_analytics(self):
        """Analytics endpoint — hits PostgreSQL aggregation."""
        self.client.get("/api/analytics", name="/api/analytics")