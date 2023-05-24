from fastapi import APIRouter, HTTPException
from enum import Enum
from fastapi.params import Query
from src import database as db
from pydantic import BaseModel, Field
from typing import List
import sqlalchemy


class FighterJson(BaseModel):
    first_name: str | None = Field(default="", alias='first_name')
    last_name: str | None = Field(default="", alias='last_name')
    height: int | None = 0
    reach: int | None = 0
    stance_id: int | None = Field(default=None, alias='stance_id')


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
    * `weight`: The weight class of the most recent fight the fighter has participated in.
    * `wins`: The amount of wins the fighter has in UFC events,
    * `losses`: The amount of losses the fighter has in UFC events.
    * `draws`: The amount of draws the fighter has in UFC events.
    * `recent_fights`: A list of the 5 most recent fights the fighter participated in. The list is descending ordered based on recency.

    Each fight is represented by a dictionary with the following keys:
    * `fight_id`: The internal id of the fight.
    * `event`: The name of the event the fight took place at.
    * `opponent_id`: The internal id of the opponent.
    * `opponent_name`: The name of the opponent.
    * `result`: The result of the match, if known, along with the method of victory.
    """
    fighter_info = sqlalchemy.text(
        """
        WITH recent_fights AS (
            SELECT fight_id, fighter1_id, fighter2_id, class AS weight, result, event_date, event_name, method
            FROM fights
                INNER JOIN events ON fights.event_id = events.event_id
                INNER JOIN weight_classes ON weight_class = weight_classes.id
                LEFT JOIN victory_methods ON fights.method_of_vic = victory_methods.id
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
                weight,
                event_name,
                method,
                result
            FROM fighters
                LEFT JOIN stances ON
                    fighters.stance_id = stances.id
                LEFT JOIN recent_fights ON fighter_id = fighter1_id OR fighter_id = fighter2_id
            WHERE fighter_id = (:id)
        ), opponent_info AS (
            SELECT
                CONCAT(fighters.first_name, ' ', fighters.last_name) AS opname,
                fighters.fighter_id AS op_id,
                fight_id AS fight_id2
            FROM fighters
                INNER JOIN fighter_info
                    ON fighter_info.fighter_id != fighters.fighter_id
                        AND (fighter_info.fighter1_id = fighters.fighter_id OR fighter_info.fighter2_id = fighters.fighter_id)
        )
        SELECT
            *,
            (SELECT COUNT(*) FROM fighter_info WHERE result = fighter_id) AS wins,
            (SELECT COUNT(*) FROM fighter_info WHERE fight_id IS NOT NULL AND result IS NULL AND method IS NOT NULL) AS draws,
            (SELECT COUNT(*) FROM fighter_info WHERE result != fighter_id AND result IS NOT NULL AND method IS NOT NULL) AS losses
        FROM fighter_info
            LEFT JOIN opponent_info
                ON fight_id = fight_id2
        LIMIT 5;
        """
    )

    with db.engine.connect() as conn:
        result = conn.execute(fighter_info, [{"id": id}])
        rows = result.fetchall()
        if not rows:
            raise HTTPException(status_code=404, detail="fighter not found")
        
        recent_matches = []
        for row in rows:
            print(row)
            if not row.fight_id:
                # No fights, no point.
                break
            if row.result == row.op_id:
                decision = "Loss - (" + row.method + ")"
            elif row.result == id:
                decision = "Win - (" + row.method + ")"
            elif row.result is None and row.method is not None:
                decision = "Draw - (" + row.method + ")"
            elif row.result is None and row.method is None:
                decision = "Unknown"
            recent_matches.append(
                {
                    "fight_id": row.fight_id,
                    "event": row.event_name,
                    "opponent_id": row.op_id,
                    "opponent_name": row.opname.strip(),
                    "result": decision,
                }
            )

        fighter_row = rows[0]
        fighter = {
            "fighter_id": id,
            "name": fighter_row.name.strip(),
            "height": fighter_row.height,
            "reach": fighter_row.reach,
            "stance": fighter_row.stance,
            "weight": fighter_row.weight,
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
    weight_class: str = "",
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
    * `W/D/L`: The win-draw-lose score of the fighter in UFC events.

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
    * `weight_class`: Only fighters who have participated in this weight class.
    
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
                class AS weight_class,
                COUNT(*) FILTER(WHERE fighter_id = result) OVER (PARTITION BY fighter_id) AS wins,
                COUNT(*) FILTER(WHERE result IS NULL AND method_of_vic IS NOT NULL) OVER (PARTITION BY fighter_id) AS draws,
                COUNT(*) FILTER(WHERE result != fighter_id AND RESULT IS NOT NULL AND method_of_vic IS NOT NULL)
                    OVER (PARTITION BY fighter_id) AS losses
            FROM fighters
                LEFT JOIN stances ON fighters.stance_id = stances.id
                LEFT JOIN fights ON fighters.fighter_id = fights.fighter1_id
                    OR fighters.fighter_id = fights.fighter2_id
                INNER JOIN events ON events.event_id = fights.event_id
                INNER JOIN weight_classes ON fights.weight_class = weight_classes.id
            WHERE CONCAT(first_name, ' ', last_name) ILIKE :name
                AND event_name ILIKE :event
                AND stance ILIKE :stance
                AND class ILIKE :weight_class
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
        + """
        LIMIT (:limit)
        OFFSET (:offset);
        """
    ).bindparams(
        sqlalchemy.bindparam('name', '%' + name + '%'),
        sqlalchemy.bindparam('stance', '%' + stance + '%'),
        sqlalchemy.bindparam('event', '%' + event + '%'),
        sqlalchemy.bindparam('weight_class', '%' + weight_class + '%'),
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
        sqlalchemy.bindparam('limit', limit),
        sqlalchemy.bindparam('offset', offset),
    )
    with db.engine.connect() as conn:
        result = conn.execute(fighters)
        json = []
        for row in result:
            wdl = str(row.wins) + "/" + str(row.draws) + "/" + str(row.losses)
            json.append(
                {
                    "fighter_id": row.fighter_id,
                    "name": row.name.strip(),
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
    This endpoint takes a fighter datatype and adds new data into the database.
    The fighter is represented by their first and last name, their height in inches,
    their reach in inches, and their stance represented by its stance_id
    (1 = Orthodox, 2 = Southpaw, 3 = Switch).

    This endpoint ensures that the `stance_id` is either null or a correct enumeration, that
    the `height` and `reach` is within the bounds of 0 to 9999. Besides from stance, no other
    value should be given as null.

    If there exists a fighter with the same name (concatenation of first and last, case-
    insensitive), height, weight, and stance, then the data requested is regarded as 
    duplicate and will be voided.

    The endpoint returns the id of the resulting fighter that was created.
    """
    if fighter.stance_id is None:
        stance = None
    elif fighter.stance_id not in [1, 2, 3]:
        raise HTTPException(status_code=400, detail="improper stance given")
    else:
        stance = fighter.stance_id
    
    if fighter.height < 0 or fighter.height > 9999 or fighter.height is None:
        raise HTTPException(status_code=400, detail="improper height given")
    
    if fighter.reach < 0 or fighter.reach > 9999 or fighter.reach is None:
        raise HTTPException(status_code=400, detail="improper reach given")

    if fighter.first_name is None:
        raise HTTPException(status_code=400, detail="improper first name given")
    if fighter.last_name is None:
        raise HTTPException(status_code=400, detail="improper last name given")

    check_duplicate = sqlalchemy.text(
        """
        SELECT first_name, last_name, height, reach, stance_id
        FROM fighters
        WHERE LOWER(CONCAT(first_name, last_name)) = LOWER(CONCAT(:first_name, :last_name))
            AND height = (:height)
            AND reach = (:reach)
            AND (stance_id IS NULL OR stance_id = (:stance))
        """
    )

    with db.engine.begin() as conn:
        check = conn.execute(check_duplicate, [{"first_name": fighter.first_name,
                                                "last_name": fighter.last_name,
                                                "height": fighter.height,
                                                "reach": fighter.reach,
                                                "stance": stance}])
        if check.first() is not None:
            raise HTTPException(status_code=409, detail="duplicate data given")
        result = conn.execute(
            sqlalchemy.insert(db.fighters)
            .values(first_name=fighter.first_name,
                    last_name=fighter.last_name,
                    height=fighter.height,
                    reach=fighter.reach,
                    stance_id=stance)
        )

    return {"fighter_id": result.inserted_primary_key[0]}


@router.put("/fighters/{fighter_id}", tags=["fighters"])
def update_fighter(fighter_id: int, fighter: FighterJson):
    """
    This endpoint takes a `fighter_id` and a fighter model to update the data
    of the `fighter_id` in the database.

    Partial updates are possible by simply not providing values to update.

    No data value should be given as null. Additionally,`stance_id` is 
    enforced to still be between 1-3, representing Orthodox, Southpaw,
    or Switch respectively.

    Upon success, this endpoint returns the newly modified model.
    """
    stored_fighter_data = (
        sqlalchemy.select(
            db.fighters.c.first_name,
            db.fighters.c.last_name,
            db.fighters.c.height,
            db.fighters.c.reach,
            db.fighters.c.stance_id
        )
        .where(db.fighters.c.fighter_id == fighter_id)
    )
    if fighter.stance_id is not None and (fighter.stance_id < 1 or fighter.stance_id > 3):
        raise HTTPException(status_code=400, detail='stance_id must be between 1 and 3 or left as null')

    with db.engine.connect() as conn:
        result = conn.execute(stored_fighter_data)
        if result is None:
            raise HTTPException(status_code=404, detail='fighter does not exist')
        for row in result:
            stored_fighter_model = FighterJson(**row._mapping)
            update_data = fighter.dict(exclude_unset=True)
            updated_fighter = stored_fighter_model.copy(update=update_data)
            result = conn.execute(
                sqlalchemy.update(db.fighters)
                .where(db.fighters.c.fighter_id == fighter_id)
                .values(updated_fighter.dict())
            )
            conn.commit()
            break

    return updated_fighter