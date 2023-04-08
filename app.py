import asyncio
import decimal
import time
from typing import Any

import uvicorn as uvicorn
from fastapi import FastAPI, HTTPException, Depends

from rabbit.client import Rabbit
from db.schemas import Event, Status


events: dict[str, Event] = {
    "1": Event(
        event_id="1",
        coefficient=decimal.Decimal("1.20"),
        deadline=int(time.time()) + 600,
        status=Status.NEW,
    ),
    "2": Event(
        event_id="2",
        coefficient=decimal.Decimal("1.15"),
        deadline=int(time.time()) + 60,
        status=Status.NEW,
    ),
    "3": Event(
        event_id="3",
        coefficient=decimal.Decimal("1.67"),
        deadline=int(time.time()) + 90,
        status=Status.NEW,
    ),
    "4": Event(
        event_id="4",
        coefficient=decimal.Decimal("1.67"),
        deadline=int(time.time()),
        status=Status.NEW,
    ),
}


app = FastAPI()
rmq = Rabbit()


@app.on_event("startup")
def startup() -> None:
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(rmq.setup(loop))
    asyncio.ensure_future(rmq.consume_messages())


@app.post("/event", status_code=201)
async def create_event(event: Event) -> Event:
    if event.event_id not in events:
        events[event.event_id] = event
        return event
    raise HTTPException(409, detail="Event id should be unique")


@app.put("/event", status_code=200)
async def update_event(event: Event, rabbit: Rabbit = Depends(rmq)) -> dict:
    if event.event_id in events:
        for p_name, p_value in event.dict(exclude_unset=True).items():
            setattr(events[event.event_id], p_name, p_value)
        await rabbit.publish(event.json())
        return {}
    raise HTTPException(404, detail="Event not found")


@app.get("/event/{event_id}")
async def get_event(event_id: str) -> Event:
    if event_id in events:
        return events[event_id]
    raise HTTPException(status_code=404, detail="Event not found")


@app.get("/events")
async def get_events() -> list[Event]:
    return list(e for e in events.values() if time.time() < e.deadline)  # type: ignore


if __name__ == "__main__":
    uvicorn.run(app=app, port=8000, host="0.0.0.0")
