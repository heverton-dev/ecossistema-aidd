from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def view_store(self):
        self.client.get("/")

    @task(5)
    def list_products(self):
        self.client.get("/api/produtos")

    @task(1)
    def view_docs(self):
        self.client.get("/docs")
