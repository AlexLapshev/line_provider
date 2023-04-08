import time
from copy import copy
from unittest.mock import MagicMock

import pytest
from httpx import AsyncClient

from app import app, rmq, events
from db.schemas import Event


class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)


app.dependency_overrides[rmq] = lambda: AsyncMock()


@pytest.mark.parametrize("anyio_backend", ["asyncio"])
async def test_simple_workflow(anyio_backend):
    test_id = "test_id"

    test_event = {
        "event_id": test_id,
        "coefficient": 1.0,
        "deadline": int(time.time()) + 600,
        "status": 1,
    }

    async with AsyncClient(app=app, base_url="http://localhost") as ac:
        create_response = await ac.post("/event", json=test_event)

    assert create_response.status_code == 201
    t_e = copy(test_event)

    async with AsyncClient(app=app, base_url="http://localhost") as ac:
        t_e["coefficient"] = 1
        create_response = await ac.post("/event", json=t_e)
        assert create_response.status_code == 422

    async with AsyncClient(app=app, base_url="http://localhost") as ac:
        t_e["coefficient"] = 1.333
        create_response = await ac.post("/event", json=t_e)
        assert create_response.status_code == 422

    async with AsyncClient(app=app, base_url="http://localhost") as ac:
        create_response = await ac.post("/event", json=test_event)
    assert create_response.status_code == 409

    async with AsyncClient(app=app, base_url="http://localhost") as ac:
        response = await ac.get(f"/event/{test_id}")

    assert response.status_code == 200
    assert response.json() == test_event

    updated_event = test_event.copy()
    updated_event["status"] = 2
    async with AsyncClient(app=app, base_url="http://localhost") as ac:
        update_response = await ac.put(
            "/event", json={"event_id": test_id, "status": 2}
        )

    assert update_response.status_code == 200

    async with AsyncClient(app=app, base_url="http://localhost") as ac:
        update_response = await ac.put(
            "/event", json={"event_id": "no_id", "status": 2}
        )

    assert update_response.status_code == 404

    async with AsyncClient(app=app, base_url="http://localhost") as ac:
        update_response = await ac.put(
            "/event", json={"event_id": "no_id", "coefficient": 2}
        )

    assert update_response.status_code == 422

    async with AsyncClient(app=app, base_url="http://localhost") as ac:
        update_response = await ac.put(
            "/event", json={"event_id": "no_id", "coefficient": 2.222}
        )

    assert update_response.status_code == 422

    async with AsyncClient(app=app, base_url="http://localhost") as ac:
        response = await ac.get(f"/event/{test_id}")

    assert response.status_code == 200
    assert response.json() == updated_event

    async with AsyncClient(app=app, base_url="http://localhost") as ac:
        response = await ac.get(f"/event/dummy")

    assert response.status_code == 404

    async with AsyncClient(app=app, base_url="http://localhost") as ac:
        response = await ac.get(f"/events")

    assert response.status_code == 200
    assert [Event(**e) for e in response.json()][:3] == [
        e.dict() for _, e in events.items()
    ][:3]
