from fastapi import APIRouter, HTTPException
from enum import Enum
from src import database as db
from fastapi.params import Query

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
    print(event_id)

    try:
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

        return json
    except Exception:
        raise HTTPException(status_code=404, detail="event not found.")




# Add get parameters
@router.post("/events/{event_id}", tags=["events"])
def add_event(event_id: int):
    stmt = (
        db.sqlalchemy.text("""
        INSERT INTO events (event_id, event_name, event_date, venue, attendance) VALUES (:val1, :val2, :val3, :val4, :val5)
        """
        )
    )

    try:
        with db.engine.connect() as conn:
            conn.execute(stmt, {"val1": event_id, "val2": 'test2', "val3": '2023-05-08', "val4": "test2", "val5": 100})
            conn.commit()
            conn.close()
        return event_id
    except Exception:
        raise HTTPException(status_code=402, detail="")
