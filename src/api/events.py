from datetime import datetime

import sqlalchemy
from fastapi import APIRouter, HTTPException
from enum import Enum

from pydantic import BaseModel, Field

from src import database as db

router = APIRouter()


@router.get("/events/{event_id}", tags=["events"])
def get_event(event_id: int):
    """
    This endpoint returns all the fights in a event that is queried by its id.
    For each event it returns:

    * `event_name`: The name of the event.
    * `event_date`: The date of the event.
    * `venue`: The place where the event was held.
    * `attendance`: The number of audience.
    """
    stmt = (
        db.sqlalchemy.text("""
        select event_name, event_date, venue, attendance
        from events
        where event_id = :id
        """)
    )

    with db.engine.connect() as conn:
        json = []
        result = conn.execute(stmt, {"id": event_id})
        for row in result:
            json.append(
                {
                    "event_name": row.event_name,
                    "event_date": row.event_date,
                    "venue": row.venue,
                    "attendance": row.attendance,
                }
            )
        if not json:
            raise HTTPException(status_code=404, detail="event not found.")
    return json


@router.get("/events/", tags=["events"])
def get_fights_event(event_name: str):
    """
    This endpoint returns all the fights in a event that is queried by its id.
    For each event it returns:

    * `fighter1`: One of the fighter in the fight
    * `fighter2`: The other fighter in the fight
    * `result`: The result of the fight
    * `event_name`: The name of the event.
    * `event_date`: The date of the event.
    * `venue`: The place where the event was held.
    """
    stmt = (
        db.sqlalchemy.text("""
        select f1.first_name fighter1, f2.first_name fighter2, result, event_name, event_date, venue
        from fights ft
        join fighters f1 on f1.fighter_id = ft.fighter1_id
        join fighters f2 on f2.fighter_id = ft.fighter2_id
        join events e on e.event_id = ft.event_id
        where e.event_name = :name
        order by fight_id
        """
                           )
    )

    with db.engine.connect() as conn:
        json = []
        result = conn.execute(stmt, [{"name": event_name}])
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


def is_valid_date_format(date_string):
    """
    This endpoint checks if the date_string is formatted in "YYYY-MM-DD"
    """
    try:
        datetime.strptime(date_string, "%Y-%m-%d")
        return True
    except ValueError:
        return False


# Add get parameters
@router.post("/events/", tags=["events"])
def add_event(event: EventJson):
    """
    This endpoint takes an event datatype and adds new data into the database.
    The event is represented by its event_name, event_date,
    venue, and attendance.

    This endpoint ensures that if event_name or event_date or venue is null,
    an error would be raised

    The endpoint returns the id of the resulting event that was created.
    """
    if event.event_name == "":
        raise HTTPException(status_code=400, detail="event_name cannot be null")
    elif event.event_date == "":
        raise HTTPException(status_code=400, detail="event_date cannot be null")
    elif event.venue == "":
        raise HTTPException(status_code=400, detail="venue cannot be null")
    elif is_valid_date_format(event.event_date) is False:
        raise HTTPException(status_code=400, detail="improper event_date given")

    with db.engine.connect() as conn:
        result = conn.execute(
            sqlalchemy.select(
                sqlalchemy.func.max(db.events.c.event_id),
            )
        )
        event_id = result.first().max_1 + 1
        conn.execute(
            sqlalchemy.insert(db.events)
                .values(event_id=event_id,
                        event_name=event.event_name,
                        event_date=event.event_date,
                        venue=event.venue,
                        attendance=event.attendance,
                        )
        )
        conn.commit()
        conn.close()
    return {"event_id": event_id}
