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
    stance: int = Field(default=None, alias='stance')


router = APIRouter()


@router.get("/fighters/{id}", tags=["fighters"])
def get_fighter(id: int):
    """
    This endpoint returns a fighter by their internal id.
    For each fighter it returns:

    * `fighter_id`: The internal id of the fighter.
    * `name`: The name of the fighter, in the format of [First Name Last Name].
    * `height`: The height of the fighter in inches.
    * `weight`: The weight of the fighter from their most recent weigh-in in pounds.
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
    stmt = (
        sqlalchemy.select(
            db.fighters.c.fighter_id,
            sqlalchemy.sql.functions.concat(
                db.fighters.c.first_name + " " + db.fighters.c.last_name
            ).label("name"),
            db.fighters.c.height,
            db.fighter_stats.c.weight,
            db.fighters.c.reach,
            db.stances.c.stance,
        )
        .join(db.stances, db.fighters.c.stance == db.stances.c.id, isouter=True)
        .join(db.fights, (db.fighters.c.fighter_id == db.fights.c.fighter1_id)
                         | (db.fighters.c.fighter_id == db.fights.c.fighter2_id), isouter=True)
        .join(db.fighter_stats, db.fighter_stats.c.fighter_id == db.fighters.c.fighter_id, isouter=True)
        .where(db.fighters.c.fighter_id == id)
        .group_by(db.fighters.c.fighter_id, db.fighter_stats.c.stats_id, db.stances.c.stance, 
                  db.fights.c.fight_id)
        .order_by(sqlalchemy.desc(db.fighter_stats.c.stats_id), sqlalchemy.desc(db.fights.c.fight_id))
    )
    stmt2 = sqlalchemy.text(
        """
        SELECT
            fight_id,
            result,
            fighter1_id,
            fighter2_id,
            stats_1,
            stats_2,
            fighter_id,
            first_name,
            last_name
        FROM fights
            INNER JOIN fighters
            ON (fighter1_id = fighter_id and fighter1_id != (:id))
                or (fighter2_id = fighter_id and fighter2_id != (:id))
        WHERE fighter1_id = (:id) or fighter2_id = (:id)
        ORDER BY fight_id DESC
        LIMIT 5
        """
    )

    with db.engine.connect() as conn:
        result = conn.execute(stmt)
        fighter_row = result.first()
        print(fighter_row)
        if fighter_row is None:
            raise HTTPException(status_code=404, detail="fighter not found")
        
        recent_matches = []
        result = conn.execute(stmt2, [{"id": id}])
        for row in result:
            opponent = row.fighter1_id if row.fighter2_id == id else row.fighter2_id
            if row.fighter_id == opponent:
                recent_matches.append({
                        "fight_id": row.fight_id,
                        "opponent_id": opponent,
                        "opponent_name": row.first_name + " " + row.last_name,
                        "result": row.result,
                    }
                )
            
        result = conn.execute(
            sqlalchemy.text(
            """
            SELECT
                (SELECT COUNT(*) FROM fights WHERE result = (:id)) as wins,
                (SELECT COUNT(*)
                 FROM fights
                 WHERE result is null
                   and (fighter1_id = (:id) or fighter2_id = (:id))) as draws,
                ROW_NUMBER() OVER (ORDER BY fight_id) AS relational_fight_total
            FROM fights
            WHERE fighter1_id = (:id) or fighter2_id = (:id)
            ORDER BY fight_id DESC
             """
            ),[{"id": id}]
        )
        results = result.first()
        if results == None:
            wins = 0
            losses = 0
            draws = 0
        else:
            wins = results.wins
            losses = results.relational_fight_total - results.wins - results.draws
            draws = results.draws
        fighter = {
            "fighter_id": id,
            "name": fighter_row.name,
            "height": fighter_row.height,
            "weight": fighter_row.weight,
            "reach": fighter_row.reach,
            "stance": fighter_row.stance,
            "wins": wins,
            "losses": losses,
            "draws": draws,
            "recent_fights": recent_matches,
        }
    
    return fighter


class fighter_sort_options(str, Enum):
    name = "name"
    height = "height"
    weight = "weight"
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
    weight_min: int = Query(0, ge=0, le=9999),
    weight_max: int = Query(9999, ge=0, le=9999),
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
    * `weight`: The most recent recorded weight of the fighter in pounds.
    * `reach`: The reach of the fighter in inches.
    * `stance`: The stance of the fighter.
    * `W/D/L`: The win-draw-lose score of the fighter.

    Available filters are:
    * `stance`: The stance of the fighter.
    * `name`: Inclusive search on the name string.
    * `height_min`: Minimum height in inches (inclusive). Defaults to 0.
    * `height_max`: Maximum height in inches (inclusive). Defaults to 999.
    * `weight_min`: Minimum weight in pounds (inclusive). Defaults to 0.
    * `weight_max`: Maximum weight in pounds (inclusive). Defaults to 9999.
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
    * `weight` - Sorts by weight.
    * `reach` - Sorts by reach.
    * `order` - Either "ascending" or "descending".
    
    The `limit` and `offset` query parameters are used for pagination. limit will limit the amount
    of results to return and offset species the number of results to skip before returning the result.
    """
    stmt = sqlalchemy.text(
        """
        SELECT fighter_id, weight
        FROM (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY fighter_stats.fighter_id ORDER BY fighter_stats.stats_id DESC) AS n
            FROM fighter_stats
        ) AS x
        WHERE n <= 1
        """
    )
    stmt = stmt.columns(
        sqlalchemy.column('fighter_id'),
        sqlalchemy.column('weight'),
    ).subquery("wt")

    if sort is fighter_sort_options.name:
        order_by = sqlalchemy.sql.functions.concat(
                db.fighters.c.first_name + " " + db.fighters.c.last_name
            ).label("name")
    elif sort is fighter_sort_options.height:
        order_by = db.fighters.c.height
    elif sort is fighter_sort_options.weight:
        order_by = stmt.c.weight
    elif sort is fighter_sort_options.reach:
        order_by = db.fighters.c.reach
    else:
        assert False
    
    if order == fighter_order_options.ascending:
        order_by = sqlalchemy.asc(order_by)
    elif order == fighter_order_options.descending:
        order_by = sqlalchemy.desc(order_by)
    else:
        assert False

    stmt = (
        sqlalchemy.select(
            db.fighters.c.fighter_id,
            sqlalchemy.sql.functions.concat(
                db.fighters.c.first_name + " " + db.fighters.c.last_name
            ).label("name"),
            db.fighters.c.height,
            stmt.c.weight,
            db.fighters.c.reach,
            db.stances.c.stance,
            db.events.c.event_id
        )
        .select_from(db.fighters)
        .join(stmt, db.fighters.c.fighter_id == stmt.c.fighter_id, isouter=True)
        .join(db.stances, db.fighters.c.stance == db.stances.c.id, isouter=True)
        .join(db.fights, (db.fighters.c.fighter_id == db.fights.c.fighter1_id)
                         | (db.fighters.c.fighter_id == db.fights.c.fighter2_id), isouter=True)
        .join(db.events, db.fights.c.event_id == db.events.c.event_id, isouter=True)
        .order_by(order_by, db.fighters.c.fighter_id)
        .limit(limit)
        .offset(offset)
    )

    # filter only if params are passed
    if name != "":
        stmt = stmt.where(sqlalchemy.sql.functions.concat(
                db.fighters.c.first_name + " " + db.fighters.c.last_name
            ).label("name").ilike(f"%{name}%"))
    if stance != "":
        stmt = stmt.where(db.stances.c.stance.ilike(f"%{stance}%"))
    if height_min != 0:
        stmt = stmt.where(db.fighters.c.height >= height_min)
    if height_max != 999:
        stmt = stmt.where(db.fighters.c.height <= height_max)
    if weight_min != 0:
        stmt = stmt.where(sqlalchemy.column('weight') >= weight_min)
    if weight_max != 9999:
        stmt = stmt.where(sqlalchemy.column('weight') <= weight_max)
    if reach_min != 0:
        stmt = stmt.where(db.fighters.c.reach >= reach_min)
    if reach_max != 999:
        stmt = stmt.where(db.fighters.c.reach <= reach_max)
    if event != "":
        stmt = stmt.where(db.events.c.event_name.ilike(f"%{event}"))

    print(stmt)

    with db.engine.connect() as conn:
        result = conn.execute(stmt)
        json = []
        for row in result:
            results = conn.execute(
                sqlalchemy.text(
                """
                SELECT
                    (SELECT COUNT(*) FROM fights WHERE result = (:id)) as wins,
                    (SELECT COUNT(*)
                    FROM fights
                    WHERE result is null
                    and (fighter1_id = (:id) or fighter2_id = (:id))) as draws,
                    ROW_NUMBER() OVER (ORDER BY fight_id) AS relational_fight_total
                FROM fights
                WHERE fighter1_id = (:id) or fighter2_id = (:id)
                ORDER BY fight_id DESC
                """
                ),[{"id": row.fighter_id}]
            )
            results = results.first()
            if results == None:
                wins = 0
                losses = 0
                draws = 0
            else:
                wins = results.wins
                losses = results.relational_fight_total - results.wins - results.draws
                draws = results.draws
            if ((wins_min != 0 and wins < wins_min)
                or (losses_min != 0 and losses < losses_min)
                or (draws_min != 0 and draws < draws_min)):
                continue
            if ((wins_max != 9999 and wins > wins_max)
                or (losses_min != 9999 and losses > losses_max)
                or (draws_min != 9999 and draws > draws_max)):
                continue
            wdl = str(wins) + "/" + str(draws) + "/" + str(losses)
            json.append(
                {
                    "fighter_id": row.fighter_id,
                    "name": row.name,
                    "height": row.height,
                    "weight": row.weight,
                    "reach": row.reach,
                    "stance": row.stance,
                    "W/D/L": wdl,
                    "event_iid": row.event_id,
                }
            )

    return json


@router.post("/fighters/", tags=["fighters"])
def add_fighter(fighter: FighterJson):
    """
    This endpoint takes an fighter datatype and adds new data into the database.
    The fighter is represented by their first and last name, their height in inches,
    their reach in inches, and their stance represented by its stance_id.

    This endpoint ensures that the stance is either None or a correct enumeration, that
    the height is within the bounds of 0 to 9999, and that the reach is within the bounds
    of 0 to 99.9.

    The endpoint returns the id of the resulting fighter that was created.
    """
    # Ensure the identity key is after the max id
    with db.engine.connect() as conn:
        result = conn.execute(
            sqlalchemy.text(
                """
                SELECT setval(pg_get_serial_sequence('fighters', 'fighter_id'), max(fighter_id))
                FROM fighters"""
            )
        )

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
            sqlalchemy.select(
                sqlalchemy.sql.functions.max(db.fighters.c.fighter_id),
            )
        )
        fighter_id = result.first().max_1 + 1
        conn.execute(
            sqlalchemy.insert(db.fighters)
            .values(first_name=fighter.first_name,
                    last_name=fighter.last_name,
                    height=fighter.height,
                    reach=fighter.reach,
                    stance=stance)
        )
    
    return {"fighter_id": fighter_id}
