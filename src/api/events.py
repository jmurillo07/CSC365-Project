from datetime import datetime

import sqlalchemy
from fastapi import APIRouter, HTTPException
from enum import Enum

from pydantic import BaseModel, Field

from src import database as db


class EventJson(BaseModel):
    event_name: str = Field(default="", alias='event_name')
    event_date: str = Field(default="", alias='event_date')
    venue_id: int
    attendance: int = Field(default=None, alias='attendance')


router = APIRouter()


@router.get("/events/{event_id}", tags=["events"])
def get_event(event_id: int):
    """
    This endpoint returns event information given an `event_id`.
    For each event it returns:

    * `event_name`: The name of the event.
    * `event_date`: The date of the event.
    * `venue`: The name of the place where the event was held.
    * `attendance`: The number of people recorded to have attended the event.
    """
    stmt = (
        sqlalchemy.text(
        """
        SELECT event_name, event_date, venue_name, attendance
        FROM events
            INNER JOIN venue ON events.venue_id = venue.venue_id
        WHERE event_id = (:id)
        """
        )
    )

    with db.engine.connect() as conn:
        json = []
        result = conn.execute(stmt, {"id": event_id})
        for row in result:
            json.append(
                {
                    "event_name": row.event_name,
                    "event_date": row.event_date,
                    "venue": row.venue_name,
                    "attendance": row.attendance,
                }
            )
        if not json:
            raise HTTPException(status_code=404, detail="event not found.")

    return json


@router.get("/events/", tags=["events", "fights"])
def get_fights_by_event(event_name: str):
    """
    This endpoint returns all the fights whose corresponding event name is similar to
    the given string.
    For each fight it returns:

    * `fight_id`: The internal id of the fight.
    * `fighter1`: The name of one fighter in the fight.
    * `fighter2`: The name of the second figher in the fight.
    * `result`: The result of the fight.
    * `event_name`: The event the fight is from.
    * `event_id`: The internal id of the event.
    * `event_date`: The date the fight took place (YYYY-MM-DD).
    * `venue`: The name of the place where the event was held.

    The endpoint returns the fights by descending `event_date` and by ascending the internal
    id of the fight.
    """
    fights = sqlalchemy.text("""
        SELECT
            fight_id,
            CONCAT(f1.first_name, ' ', f1.last_name) AS fighter1,
            f1.fighter_id AS f1_id,
            CONCAT(f2.first_name, ' ', f2.last_name) AS fighter2,
            f2.fighter_id AS f2_id,
            method, 
            result,
            event_name,
            fights.event_id,
            DATE(event_date) as date,
            venue_name
        FROM fights
            INNER JOIN fighters AS f1 ON f1.fighter_id = fights.fighter1_id
            INNER JOIN fighters AS f2 ON f2.fighter_id = fights.fighter2_id
            INNER JOIN events ON events.event_id = fights.event_id
            INNER JOIN venue ON venue.venue_id = events.venue_id
            LEFT JOIN victory_methods ON fights.method_of_vic = victory_methods.id
        WHERE event_name ILIKE :name
        ORDER BY DATE(event_date) DESC, fight_id
        """
    ).bindparams(
        sqlalchemy.bindparam('name', '%' + event_name + '%')
    )

    with db.engine.connect() as conn:
        result = conn.execute(fights)
        rows = result.fetchall()
        json = []
        for row in rows:
            if not row.event_name:
                # No fights, no point.
                break
            if row.result == row.f1_id:
                decision = "Win - " + row.fighter1 + " - (" + row.method + ")"
            elif row.result == row.f2_id:
                decision = "Win - " + row.fighter2 + " - (" + row.method + ")"
            elif row.result is None and row.method is not None:
                decision = "Draw - (" + row.method + ")"
            elif row.result is None and row.method is None:
                decision = "Unknown"
            json.append(
                {
                    "fight_id": row.fight_id,
                    "fighter1": row.fighter1,
                    "fighter2": row.fighter2,
                    "result": decision,
                    "event_name": row.event_name,
                    "event_id": row.event_id,
                    "event_date": row.date,
                    "venue": row.venue_name,
                }
            )

    return json


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
    The event is represented by its `event_name`, `event_date`,
    `venue_id`, and `attendance`.

    This endpoint ensures that if `event_name` or `event_date` is null,
    an error would be raised.

    Additionally, it ensures that the `venue_id` actually exists and that `event_date`
    is in the format of "YYYY-MM-DD".

    The endpoint returns the id of the resulting event that was created.
    """
    if event.event_name == "":
        raise HTTPException(status_code=400, detail="event_name cannot be null")
    elif event.event_date == "":
        raise HTTPException(status_code=400, detail="event_date cannot be null")
    elif not is_valid_date_format(event.event_date):
        raise HTTPException(status_code=400, detail="improper event_date given")

    with db.engine.begin() as conn:
        result = conn.execute(
            sqlalchemy.select(
                db.venue.c.venue_id,
            ).where(db.venue.c.venue_id == event.venue_id)
        )
        if result.fetchone is None:
            raise HTTPException(status_code=404, detail="given venue_id doesn't exist")

        result = conn.execute(
            sqlalchemy.insert(db.events)
            .values(
                event_name=event.event_name,
                event_date=event.event_date,
                venue_id=event.venue_id,
                attendance=event.attendance,
            )
        )

    return {"event_id": result.inserted_primary_key[0]}
