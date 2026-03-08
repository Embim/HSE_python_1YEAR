# Запуск:
#     locust -f tests/load/locustfile.py --host=http://localhost:8000

import random
import string
from locust import HttpUser, between, task


def _random_str(n: int = 8) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=n))


class URLShortenerUser(HttpUser):
    wait_time = between(0.1, 1)

    def on_start(self):
        username = _random_str()
        password = "loadtest123"
        self.client.post(
            "/register",
            json={"username": username, "email": f"{username}@test.com", "password": password},
        )
        resp = self.client.post("/login", data={"username": username, "password": password})
        token = resp.json().get("access_token", "")
        self.auth_headers = {"Authorization": f"Bearer {token}"}
        self.short_codes: list[str] = []

    @task(4)
    def create_link(self):
        url = f"https://example-{_random_str()}.com"
        resp = self.client.post(
            "/links/shorten",
            json={"original_url": url},
            headers=self.auth_headers,
        )
        if resp.status_code == 201:
            self.short_codes.append(resp.json()["short_code"])

    @task(8)
    def redirect(self):
        if not self.short_codes:
            return
        code = random.choice(self.short_codes)
        self.client.get(f"/{code}", allow_redirects=False, name="GET /{short_code}")

    @task(3)
    def get_stats(self):
        if not self.short_codes:
            return
        code = random.choice(self.short_codes)
        self.client.get(f"/links/{code}/stats", name="GET /links/{short_code}/stats")

    @task(1)
    def search_links(self):
        self.client.get(
            "/links/search",
            params={"original_url": "https://example.com"},
        )


class AnonymousUser(HttpUser):
    """Анонимные пользователи — только создание и редирект."""
    wait_time = between(0.2, 1)
    weight = 3

    def on_start(self):
        self.short_codes: list[str] = []

    @task(2)
    def create_link_anonymous(self):
        url = f"https://anon-{_random_str()}.com"
        resp = self.client.post("/links/shorten", json={"original_url": url})
        if resp.status_code == 201:
            self.short_codes.append(resp.json()["short_code"])

    @task(5)
    def redirect(self):
        if not self.short_codes:
            return
        code = random.choice(self.short_codes)
        self.client.get(f"/{code}", allow_redirects=False, name="GET /{short_code}")
