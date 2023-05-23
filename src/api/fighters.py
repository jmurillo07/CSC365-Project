from fastapi import APIRouter, HTTPException
from enum import Enum
from fastapi.params import Query
from src import database as db
from pydantic import BaseModel, Field
from typing import List
import sqlalchemy


class FighterJson(BaseModel):
    first_name: str = Field(default="", alias='first_name')
    last_name: str = Field(default="", alias='last_name')
    height: int
    reach: float
    stance_id: int = Field(default=None, alias='stance_id')


router = APIRouter()


@router.get("/fighters/{id}", tags=["fighters"])
def get_fighter(id: int):
    """
    This endpoint returns a fighter by their internal id.
    For each fighter it returns:

    * `fighter_id`: The internal id of the fighter.
    * `name`: The name of the fighter, in the format of [First Name Last Name].
    * `height`: The height of the fighter in inches.
    * `reach`: The reach of the fighter given in inches.
    * `stance`: The stance of the fighter.
    * `wins`: The amount of wins the fighter has.
    * `losses`: The amount of losses the fighter has.
    * `draws`: The amount of draws the fighter has.
    * `recent_fights`: A list of the 5 most recent fights the fighter participated in. The list is descending ordered based on recency.

    Each fight is represented by a dictionary with the following keys:
    * `fight_id`: The internal id of the fight.
    * `opponent_id`: The internal id of the opponent.
    * `opponent_name`: The name of the opponent.
    * `result`: The internal id of the victor or none if a draw.
    """
    fighter_info = sqlalchemy.text(
        """
        WITH recent_fights AS (
            SELECT fight_id, fighter1_id, fighter2_id, result, event_date
            FROM fights
                INNER JOIN events ON fights.event_id = events.event_id
            ORDER BY DATE(events.event_date) DESC
        ), fighter_info AS (
            SELECT
                fighter_id,
                CONCAT(first_name, ' ', last_name) AS name,
                height,
                reach,
                stances.stance,
                fight_id,
                fighter1_id,
                fighter2_id,
                result
            FROM fighters
                LEFT JOIN stances ON
                    fighters.stance_id = stances.id
                LEFT JOIN recent_fights ON fighter_id = fighter1_id OR fighter_id = fighter2_id
            WHERE fighter_id = (:id)
        ), opponent_info AS (
            SELECT
                CONCAT(fighters.first_name, ' ', fighters.last_name) AS opname,
                fighters.fighter_id AS op_id
            FROM fighters
                INNER JOIN fighter_info
                    ON fighter_info.fighter_id != fighters.fighter_id
                        AND (fighter_info.fighter1_id = fighters.fighter_id OR fighter_info.fighter2_id = fighters.fighter_id)
        )
        SELECT
            *,
            (SELECT COUNT(*) FROM fighter_info WHERE result = fighter_id) AS wins,
            (SELECT COUNT(*) FROM fighter_info WHERE result IS NULL) AS draws,
            (SELECT COUNT(*) FROM fighter_info WHERE result != fighter_id AND result IS NOT NULL) AS losses
        FROM fighter_info
            LEFT JOIN opponent_info
                ON fighter1_id = op_id OR fighter2_id = op_id
        LIMIT 5;
        """
    )

    with db.engine.connect() as conn:
        result = conn.execute(fighter_info, [{"id": id}])
        rows = result.fetchall()
        if rows is None:
            raise HTTPException(status_code=404, detail="fighter not found")
        
        recent_matches = []
        for row in rows:
            recent_matches.append(
                {
                    "fight_id": row.fight_id,
                    "opponent_id": row.op_id,
                    "opponent_name": row.opname,
                    "result": row.result
                }
            )

        fighter_row = rows[0]
        fighter = {
            "fighter_id": id,
            "name": fighter_row.name,
            "height": fighter_row.height,
            "reach": fighter_row.reach,
            "stance": fighter_row.stance,
            "wins": fighter_row.wins,
            "losses": fighter_row.losses,
            "draws": fighter_row.draws,
            "recent_fights": recent_matches,
        }
    
    return fighter


class fighter_sort_options(str, Enum):
    name = "name"
    height = "height"
    reach = "reach"

class fighter_order_options(str, Enum):
    ascending = "ascending"
    descending = "descending"

@router.get("/fighters/", tags=["fighters"])
def list_fighters(
    stance: str = "",
    name: str = "",
    height_min: int = Query(0, ge=0, le=999),
    height_max: int = Query(999, ge=0, le=999),
    reach_min: int = Query(0, ge=0, le=999),
    reach_max: int = Query(999, ge=0, le=999),
    wins_min: int = Query(0, ge=0, le=9999),
    wins_max: int = Query(9999, ge=0, le=9999),
    losses_min: int = Query(0, ge=0, le=9999),
    losses_max: int = Query(9999, ge=0, le=9999),
    draws_min: int = Query(0, ge=0, le=9999),
    draws_max: int = Query(9999, ge=0, le=9999),
    event: str = "",
    sort: fighter_sort_options = fighter_sort_options.name,
    order: fighter_order_options = fighter_order_options.ascending,
    limit: int = Query(50, ge=1, le=250),
    offset: int = Query(0, ge=0),
):
    """
    This endpoint takes a few filter options and returns a list of fighters matching the criteria.
    For each fighter it returns:
    * `fighter_id`: The internal id of the fighter. Can be used to query the `/fighters/{fighter_id}`
      endpoint.
    * `name`: The name of the fighter.
    * `height`: The height of the fighter in inches.
    * `reach`: The reach of the fighter in inches.
    * `stance`: The stance of the fighter.
    * `W/D/L`: The win-draw-lose score of the fighter.

    Available filters are:
    * `stance`: The stance of the fighter.
    * `name`: Inclusive search on the name string.
    * `height_min`: Minimum height in inches (inclusive). Defaults to 0.
    * `height_max`: Maximum height in inches (inclusive). Defaults to 999.
    * `reach_min`: Minimum reach in inches (inclusive). Defaults to 0.
    * `reach_max`: Maximum reach in inches (inclusive). Defaults to 9999.
    * `wins_min`: Minimum number of wins, defaults to 0.
    * `wins_max`: Maximum number of wins, defaults to 9999.
    * `losses_min`: Minimum number of losses, defaults to 0.
    * `losses_max`: Maximum number of losses, defaults to 9999.
    * `draws_min`: Minimium number of draws defaults to 0.
    * `draws_max`: Maximum number of draws, defaults to 9999.
    * `event`: Takes the name of an event and will return the fighters who participated in it.
    
    Additionally, this endpoint takes a sort query parameter:
    * `name` - Sorts alphabetically.
    * `height` - Sorts by height.
    * `reach` - Sorts by reach.
    * `order` - Either "ascending" or "descending".
    
    The `limit` and `offset` query parameters are used for pagination. limit will limit the amount
    of results to return and offset species the number of results to skip before returning the result.
    """
    if sort is fighter_sort_options.name:
        order_by = 'name'
    elif sort is fighter_sort_options.height:
        order_by = 'height'
    elif sort is fighter_sort_options.reach:
        order_by = 'reach'
    else:
        assert False
    
    if order == fighter_order_options.ascending:
        order_by += ' ASC'
    elif order == fighter_order_options.descending:
        order_by += ' DESC'
    else:
        assert False
    fighters = sqlalchemy.text(
        """
        WITH windowed AS (
            SELECT DISTINCT
                fighter_id,
                CONCAT(first_name, ' ', last_name) AS name,
                height,
                reach,
                stances.stance AS stance,
                COUNT(*) FILTER(WHERE fighter_id = result) OVER (PARTITION BY fighter_id) AS wins,
                COUNT(*) FILTER(WHERE result IS NULL) OVER (PARTITION BY fighter_id) AS draws,
                COUNT(*) FILTER(WHERE result != fighter_id AND RESULT IS NOT NULL)
                    OVER (PARTITION BY fighter_id) AS losses
            FROM fighters
                LEFT JOIN stances ON fighters.stance_id = stances.id
                LEFT JOIN fights ON fighters.fighter_id = fights.fighter1_id
                    OR fighters.fighter_id = fights.fighter2_id
                INNER JOIN events ON events.event_id = fights.event_id
            WHERE CONCAT(first_name, ' ', last_name) LIKE :name
                AND event_name LIKE :event
                AND stance LIKE :stance
                AND height BETWEEN (:height_min) AND (:height_max)
                AND reach BETWEEN (:reach_min) AND (:reach_max)
        )
        SELECT *
        FROM windowed
        WHERE wins BETWEEN (:wins_min) AND (:wins_max)
            AND draws BETWEEN (:draws_min) AND (:draws_max)
            AND losses BETWEEN (:losses_min) AND (:losses_max)
        ORDER BY 
        """
        + order_by
    ).bindparams(
        sqlalchemy.bindparam('name', '%' + name + '%'),
        sqlalchemy.bindparam('stance', '%' + stance + '%'),
        sqlalchemy.bindparam('event', '%' + event + '%'),
        sqlalchemy.bindparam('height_min', height_min),
        sqlalchemy.bindparam('height_max', height_max),
        sqlalchemy.bindparam('reach_min', reach_min),
        sqlalchemy.bindparam('reach_max', reach_max),
        sqlalchemy.bindparam('wins_min', wins_min),
        sqlalchemy.bindparam('wins_max', wins_max),
        sqlalchemy.bindparam('draws_min', draws_min),
        sqlalchemy.bindparam('draws_max', draws_max),
        sqlalchemy.bindparam('losses_min', losses_min),
        sqlalchemy.bindparam('losses_max', losses_max),
    )
    with db.engine.connect() as conn:
        result = conn.execute(fighters)
        json = []
        for row in result:
            wdl = str(row.wins) + "/" + str(row.draws) + "/" + str(row.losses)
            json.append(
                {
                    "fighter_id": row.fighter_id,
                    "name": row.name,
                    "height": row.height,
                    "reach": row.reach,
                    "stance": row.stance,
                    "W/D/L": wdl
                }
            )

    return json


@router.post("/fighters/", tags=["fighters"])
def add_fighter(fighter: FighterJson):
    """
    This endpoint takes an fighter datatype and adds new data into the database.
    The fighter is represented by their first and last name, their height in inches,
    their reach in inches, and their stance represented by its stance_id
    (1 = Orthodox, 2 = Southpaw, 3 = Switch).

    This endpoint ensures that the stance is either None or a correct enumeration, that
    the height is within the bounds of 0 to 9999, and that the reach is within the bounds
    of 0 to 99.9.

    The endpoint returns the id of the resulting fighter that was created.
    """
    if fighter.stance is None:
        stance = None
    elif fighter.stance not in [1, 2, 3]:
        raise HTTPException(status_code=400, detail="improper stance given")
    else:
        stance = fighter.stance
    
    if fighter.height < 0 or fighter.height > 9999:
        raise HTTPException(status_code=400, detail="improper height given")
    
    if fighter.reach < 0 or fighter.reach > 99.9:
        raise HTTPException(status_code=400, detail="improper reach given")

    with db.engine.begin() as conn:
        result = conn.execute(
            sqlalchemy.insert(db.fighters)
            .values(first_name=fighter.first_name,
                    last_name=fighter.last_name,
                    height=fighter.height,
                    reach=fighter.reach,
                    stance=stance)
        )
    
    return {"fighter_id": result.inserted_primary_key}
