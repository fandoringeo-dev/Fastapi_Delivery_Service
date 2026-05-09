import os
import random
from uuid import uuid4

from locust import HttpUser, between, task


class ParcelApiUser(HttpUser):
    wait_time = between(1, 3)
    host = os.getenv("LOCUST_HOST", "http://localhost:8000")

    def on_start(self) -> None:
        self.created_parcel_ids: list[str] = []
        self._create_parcel()

    def _build_create_payload(self) -> dict[str, str | int]:
        return {
            "name": f"Load parcel {uuid4().hex[:8]}",
            "weight_kg": f"{random.uniform(0.5, 20):.3f}",
            "type_id": random.choice([1, 2]),
            "declared_value_usd": f"{random.uniform(50, 2000):.2f}",
        }

    @task(5)
    def _create_parcel(self) -> None:
        response = self.client.post(
            "/api/v1/parcels/",
            json=self._build_create_payload(),
            name="POST /api/v1/parcels/",
        )

        if not response.ok:
            return

        parcel_id = response.json().get("id")
        if parcel_id:
            self.created_parcel_ids.append(parcel_id)

    @task(3)
    def read_parcels(self) -> None:
        self.client.get("/api/v1/parcels/", name="GET /api/v1/parcels/")

    @task(1)
    def read_parcel_by_id(self) -> None:
        if not self.created_parcel_ids:
            return

        parcel_id = random.choice(self.created_parcel_ids)
        self.client.get(
            f"/api/v1/parcels/{parcel_id}",
            name="GET /api/v1/parcels/:id",
        )
