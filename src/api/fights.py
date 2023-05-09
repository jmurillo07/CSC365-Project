from fastapi import APIRouter, HTTPException
from src import database as db
import sqlalchemy

router = APIRouter()

# Julian Murillo's V1 Endpoints
# goal will be to add more catch statements (illegal or invalid inserts) by V2

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

@router.post("/fights", tags = ["fights"])
def post_fight(fighter1_id: int,
               fighter2_id: int,
               round_num: int,
               round_time: str,
               event_id: int,
               result : int, 
               stats1_id: int,
               stats2_id: int,
               method_of_vic: int):
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
    # Ensure the identity key is after the max id
    with db.engine.connect() as conn:
        result = conn.execute(
            sqlalchemy.text(
                """
                SELECT setval(pg_get_serial_sequence('fights', 'fight_id'), max(fight_id))
                FROM fights"""
            )
        )

    var_dic = {
        "fighter1_id": fighter1_id,
        "fighter2_id": fighter2_id,
        "round_num": round_num,
        "round_time": round_time,
        "event_id": event_id,
        "result": result,
        "stats_1":stats1_id,
        "stats_2": stats2_id,
        "method_of_vic": method_of_vic
    }

     # Check if all the required fields are provided
    if any(field is None for field in [fighter1_id, fighter2_id, round_num, round_time,
                                       event_id, result, stats1_id, stats2_id, method_of_vic]):
        raise HTTPException(status_code=400, detail="Missing required fields")


    conn = db.engine.connect()
    stmnt = (sqlalchemy.text("""
        INSERT INTO fights (fighter1_id, fighter2_id, round_num, round_time, event_id, result, stats_1, stats_2, method_of_vic)
        VALUES (:fighter1_id, :fighter2_id, :round_num, :round_time, :event_id, :result, :stats_1, :stats_2, :method_of_vic);
        """))
    
    result = conn.execute(stmnt, var_dic)

    if result is None:
        raise HTTPException(status_code=404, detail = "fight entry failed to insert into table")

    return

    
    