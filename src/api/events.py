import sqlalchemy
from fastapi import APIRouter, HTTPException
from enum import Enum

from pydantic import BaseModel, Field

from src import database as db

router = APIRouter()



@router.get("/events/{event_id}", tags=["events"])
def get_event(event_id: int):

    stmt = (
        db.sqlalchemy.text("""
        select f1.first_name fighter1, f2.first_name fighter2, result, event_name, event_date, venue
        from fights ft
        join fighters f1 on f1.fighter_id = ft.fighter1_id
        join fighters f2 on f2.fighter_id = ft.fighter2_id
        join events e on e.event_id = ft.event_id
        where ft.event_id = :id
        order by fight_id
        """
        )
    )

    with db.engine.connect() as conn:
        json = []
        result = conn.execute(stmt, {"id": event_id})
        for row in result:
            json.append(
                {
                    "fighter1": row.fighter1,
                    "fighter2": row.fighter2,
                    "result": row.result,
                    "event_name": row.event_name,
                    "event_date": row.event_date,
                    "venue": row.venue,
                }
            )
        if not json:
            raise HTTPException(status_code=404, detail="event not found.")
    return json


class EventJson(BaseModel):
    event_name: str = Field(default="", alias='event_name')
    event_date: str = Field(default="", alias='event_date')
    venue: str = Field(default="", alias='venue')
    attendance: int = Field(default=None, alias='attendance')


# Add get parameters
@router.post("/events/", tags=["events"])
def add_event(event: EventJson):

    try:
        with db.engine.connect() as conn:
            result = conn.execute(
                sqlalchemy.select(
                    sqlalchemy.func.max(db.events.c.event_id),
                )
            )
            event_id = result.first().max_1 + 1
            conn.execute(
                sqlalchemy.insert(db.events)
                    .values(event_id = event_id,
                            event_name=event.event_name,
                            event_date=event.event_date,
                            venue=event.venue,
                            attendance=event.attendance,
                            )
            )
            conn.commit()
            conn.close()
        return {"event_id": event_id}
    except Exception:
        raise HTTPException(status_code=400, detail="Unable to insert")
