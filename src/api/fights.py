from fastapi import APIRouter, HTTPException
from src import database as db
import sqlalchemy

router = APIRouter()

# Julian Murillo's V1 Endpoints

@router.get("/fights/{fight_id}", tags = ["fights"])
def get_fights(fight_id: int):
    """
    This endpoint returns a single fight with the corresponding fight_id that was provided by the user
    query.
    """
    conn = db.engine.connect()

    stmnt = (sqlalchemy.text("""
        SELECT *
        FROM fights
        WHERE fight_id = :fight_id
        """))

    result = conn.execute(stmnt, {"fight_id" : fight_id}).fetchone()

    if result is None:
        raise HTTPException(status_code=404, detail = "line not found")
    
    fight = {
        "fight_id": result[0],
        "movie_title": result[1],
        "character": result[2],
        "line_text": result[3]
    }
    return fight

@router.post("/fights", tags = ["fights"])
def post_fight(fight_id: int,
               event: int, result: int):
    """
    The endpoint returns the fight_id of the new fight.

    Each fight is by the following fields:

    * `fight_id` : The internal id of the fight.
    * `event` : The name of the event the fight took place at.
    * `result`: The result of the fight, given as the name of the fighter or "Draw".
    * `fighter1`: The name of the first fighter.
    * `fighter2`: The name of the second fighter.
    * `kd_1`: The number of knockdowns fighter 1 got.
    * `strikes_1`: The number of strikes given fighter 1 did.
    * `td_1`: The number of takedowns fighter 1 did.
    * `sub_1`: The number of submission attempts fighter 1 did.
    * `kd_2`: The number of knockdowns fighter 2 got.
    * `strikes_2`: The number of strikes given fighter 2 did.
    * `td_2`: The number of takedowns fighter 2 did.
    * `sub_2`: The number of submission attempts fighter 2 did.
    * `weight`: The weight division of the fight.
    * `method`: The method of win.
    * `round`: The round the win happened.
    * `time`: The time during the round when the win happened.
    """
    pass