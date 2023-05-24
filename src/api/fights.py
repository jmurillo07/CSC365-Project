from fastapi import APIRouter, HTTPException
from src import database as db
import sqlalchemy
from sqlalchemy import exists, select, insert, func
from pydantic import BaseModel, Field

router = APIRouter()

# Julian Murillo's V2 Endpoints
# goal will be to add more catch statements (illegal or invalid inserts) by V3

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
        raise HTTPException(status_code=404, detail = "fight was not found")
    
    fight = {
        "fight_id": result[0],
        "fighter1_id": result[1],
        "fighter2_id": result[2],
        "round_num": result[3],
        "round_time": result[4],
        "event_id": result[5],
        "result": result[6],
        "stats1_id":result[7],
        "stats2_id": result[8],
        "method_of_vic": result[9]
    }
    return fight

class FightJson(BaseModel):
    fighter1_id: int = Field(default=0, alias='fighter1_id')
    fighter2_id: int = Field(default=0, alias='fighter2_id')
    round_num: int = Field(default=0, alias='round_num')
    round_time: str = Field(default="", alias='round_time')
    event_id: int = Field(default=0, alias='event_id')
    result: int = Field(default=0, alias='result')
    stats_1: int = Field(default=0, alias='stats_1')
    stats_2: int = Field(default=0, alias='stats_2')
    method_of_vic: int = Field(default=0, alias='method_of_vic')

@router.post("/fights", tags = ["fights"])
def post_fight(fight: FightJson):
    """
    The endpoint returns the fight_id of the new fight.
    Each fight is by the following fields:

    * `fight_id` : The internal id of the fight.
    * `fighter1_id`: The id of the first fighter.
    * `fighter2_id`: The id of the second fighter.
    * `round_num`: The round the win happened.
    * `round_time`: The time during the round when the win happened.
    * `event_id` : the id in which the event took place
    * `result`: The id of the fighter who won or NULL if the result was a draw.
    * `stats1_id`: The id of the stats table assosciated with fighter 1's performance
    * `stats2_id`: the id of the stats table assosciated with fighter 2's performance
    * `method_of_vic`: The type of victory (ex. TKO, Decision)
    """

     # Check if fighter1_id and fighter2_id are the same
    if fight.fighter1_id == fight.fighter2_id:
        raise HTTPException(status_code=400, detail="fighter1_id and fighter2_id must be different")

    # Check if the IDs and stats attributes exist in the respective tables (for some reason not working atm)
    with db.engine.begin() as conn:

        if not conn.execute(exists().where(db.fighters.c.fighter_id == fight.fighter1_id)).scalar():
            raise HTTPException(status_code=400, detail="Invalid fighter1_id")
        
        if not conn.execute(exists().where(db.fighters.c.fighter_id == fight.fighter2_id)).scalar():
            raise HTTPException(status_code=400, detail="Invalid fighter2_id")

        if not conn.execute(exists().where(db.events.c.event_id == fight.event_id)).scalar():
            raise HTTPException(status_code=400, detail="Invalid event_id")

        if not conn.execute(exists().where(db.fighter_stats.c.stats_id == fight.stats_1)).scalar():
            raise HTTPException(status_code=400, detail="Invalid stats_1")

        if not conn.execute(exists().where(db.fighter_stats.c.stats_id == fight.stats_2)).scalar():
            raise HTTPException(status_code=400, detail="Invalid stats_2")

        if not conn.execute(exists().where(db.victory_methods.c.id == fight.method_of_vic)).scalar():
            raise HTTPException(status_code=400, detail="Invalid method_of_vic")

        # Get the maximum fight_id
        result = conn.execute(
            select(func.max(db.fights.c.fight_id)).scalar()
        )
        fight_id = result.first()[0] + 1  # returned value to the user

        # Insert the fight entry into the table
        conn.execute(
            insert(db.fights)
            .values(
                fight_id=fight_id,
                fighter1_id=fight.fighter1_id,
                fighter2_id=fight.fighter2_id,
                round_num=fight.round_num,
                round_time=fight.round_time,
                event_id=fight.event_id,
                result=fight.result,
                stats_1=fight.stats_1,
                stats_2=fight.stats_2,
                method_of_vic=fight.method_of_vic
            )
        )

    if result is None:
        raise HTTPException(status_code=404, detail="Failed to insert fight entry into table")

    return {"fight_id": fight_id}
    
    