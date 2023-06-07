from fastapi import APIRouter, HTTPException
from src import database as db
import sqlalchemy
from typing import Optional
from sqlalchemy import and_, or_
from pydantic import BaseModel, Field
from datetime import datetime, timedelta


class FightJson(BaseModel):
    event_id: int = Field(default=0, alias='event_id')
    fighter1_id: int = Field(default=0, alias='fighter1_id')
    fighter2_id: int = Field(default=0, alias='fighter2_id')
    round_num: int = Field(default=1, ge=1, le=5, alias='round_num')
    round_time: str = Field(default="0:00", alias='round_time')
    result: Optional[int] = Field(default=None, alias='result')
    method_of_vic: Optional[int] = Field(default=None, ge=1, le=7, alias='method_of_vic')
    weight_class: int = Field(default=0, ge=1, le=14, alias='weight_class')


class FighterStatsJson(BaseModel):
    kd: int = Field(default=0, ge=0, alias='kd')
    strikes: int = Field(default=0, ge=0, alias='strikes')
    td: int = Field(default=0, ge=0, alias='td')
    sub: int = Field(default=0, ge=0, alias='sub')
    fighter_id: int = Field(default=0, alias='fighter_id')


router = APIRouter()


@router.get("/fights/{fight_id}", tags = ["fights"])
def get_fight(fight_id: int):
    """
    Takes in a `fight_id` and returns data associated with that internal id.
    For each fight it returns:

    * `event_name`: The name of the event the fight took place at.
    * `event_date`: The date of the event the fight took place at.
    * `fighter1`: The name of the first fighter.
    * `fighter2`: The name of the second fighter.
    * `weight_class`: The weight class of the fight.
    * `result`: The result and decision of the match.
    * `round`: The round the match ended on.
    * `round_time`: The time the round ended, given in "M:S".
    * `kd`: Given in X-X format, the left representing the knockdowns by fighter1, the right by fighter2.
    * `strikes`: Given in X-X format, the left representing the strikes landed by fighter1, the right by fighter2.
    * `td`: Given in X-X format, the left representing the takedowns by fighter1, the right by fighter2.
    * `sub`: Given in X-X format, the left representing the submission attempts by fighter1, the right by fighter2.

    Should the `fight_id` fail to be found, will raise an error.
    """
    fight = (
        sqlalchemy.select(
            db.fights.c.fight_id,
            db.events.c.event_name,
            db.events.c.event_date,
            db.fighters.c.fighter_id,
            db.fights.c.fighter1_id,
            sqlalchemy.label('full_name', db.fighters.c.first_name + ' ' + db.fighters.c.last_name),
            sqlalchemy.column('class'),
            db.fights.c.result,
            db.victory_methods.c.method,
            db.fights.c.round_num,
            db.fights.c.round_time,
            db.fighter_stats.c.kd,
            db.fighter_stats.c.strikes,
            db.fighter_stats.c.td,
            db.fighter_stats.c.sub
        ).join_from(
            db.fights, db.events, db.fights.c.event_id == db.events.c.event_id
        ).join(
            db.fighters,
            or_(db.fights.c.fighter1_id == db.fighters.c.fighter_id,
                db.fights.c.fighter2_id == db.fighters.c.fighter_id)
        ).join(
            db.victory_methods,
            db.fights.c.method_of_vic == db.victory_methods.c.id,
            isouter=True
        ).join(
            db.weight_classes,
            db.fights.c.weight_class == db.weight_classes.c.id
        ).join(
            db.fighter_stats,
            and_(
                or_(
                    db.fights.c.stats1_id == db.fighter_stats.c.stats_id,
                    db.fights.c.stats2_id == db.fighter_stats.c.stats_id
                ),
                db.fighter_stats.c.fighter_id == db.fighters.c.fighter_id
            )
        ).where(
            db.fights.c.fight_id == fight_id
        )
    )

    with db.engine.connect() as conn:
        result = conn.execute(fight).fetchall()
        if not result:
            raise HTTPException(status_code=404, detail='fight not found')

        for row in result:
            if row.fighter_id == row.fighter1_id:
                fighter1 = row.full_name
                stats1 = [row.kd, row.strikes, row.td, row.sub]
            else:
                fighter2 = row.full_name
                stats2 = [row.kd, row.strikes, row.td, row.sub]

        row = result[0]
        if row.result == row.fighter1_id:
            decision = "Win - " + fighter1 + " - (" + row.method + ")"
        elif row.result is not None:
            decision = "Win - " + fighter2 + " - (" + row.method + ")"
        elif row.result is None and row.method is not None:
            decision = "Draw - (" + row.method + ")"
        elif row.result is None and row.method is None:
            decision = "Unknown"
        
        json = {
            'event_name': row.event_name,
            'event_date': row.event_date,
            'fighter1': fighter1,
            'fighter2': fighter2,
            'weight_class': row.__getattribute__('class'),
            'result': decision,
            'round': row.round_num,
            'round_time': row.round_time,
            'kd': str(stats1[0]) + '-' + str(stats2[0]),
            'strikes': str(stats1[1]) + '-' + str(stats2[1]),
            'td': str(stats1[2]) + '-' + str(stats2[2]),
            'sub': str(stats1[3]) + '-' + str(stats2[3]),
        }

    return json

@router.post("/fights", tags = ["fights"])
def post_fight(fight: FightJson, stats1: FighterStatsJson, stats2: FighterStatsJson):
    """
    This endpoint takes in a `fight` model and two related `fighter_stats` model.
    It first adds the two `fighter_stats` data and then adds the `fight` data. The
    returned primary keys by those insertions are used to fill in `stats_1` and `stats_2`.

    `event_id` is the internal id of the event the fight is from.

    It ensures that the `fighter_id`s in the `fighter_stats` correspond with 
    `fighter1_id` and `fighter2_id` in the `fight` model, and that these `fighter_id`s
    are actually valid fighters in the database.

    `round_num` is ensured to be a number between 1-5, and `round_time`, representing
    the time spanned in the `round_num` is ensured to be a string in the format of
    M:S, and that it does not exceed 5:00.

    `result` should be either null or one of the `fighter_id`s given. A null `result` and 
    non-null `method_of_vic` indicates a draw, both being null would indicate an unknown result
    (usually an overturned one).
    Consequently, `method_of_vic` is either null or an enumeration between 1-7 representing:

    * `1`: 'SUB'
    * `2`: 'KO/TKO'
    * `3`: 'S-Dec'
    * `4`: 'M-Dec'
    * `5`: 'U-Dec'
    * `6`: 'CNC'
    * `7`: 'DQ'

    Similarly, it ensures that `weight_class` is an enumeration between 1-14 representing:

    * `1`: 'Flyweight'
    * `2`: 'Bantamweight'
    * `3`: 'Featherweight'
    * `4`: 'Lightweight'
    * `5`: 'Welterweigt'
    * `6`: 'Middleweigt'
    * `7`: 'Light Heavyweight'
    * `8`: 'Heavyweight'
    * `9`: 'Women's Strawweight'
    * `10`: 'Women's Flyweight'
    * `11`: 'Women's Bantamweight'
    * `12`: 'Women's Featherweight'
    * `13`: 'Catch Weight'
    * `14`: 'Open Weight'

    The two `fighter_stats` models takes in keys in the format:

    * `kd`: The number of knockdowns by the fighter.
    * `strikes`: The number of strikes landed by the fighter.
    * `td`: The number of takedowns by the fighter.
    * `sub`: Thenumber of submission attempts by the fighter.
    * `fighter_id`: The internal id of the fighter.

    In the event of any failure to these constraints the endpoint will error.
    Upon success, returns the `fight_id` of the newly added fight data.
    """
    # Validate the fighter_ids are consistent with each other from the given data
    if fight.fighter1_id == fight.fighter2_id:
        raise HTTPException(status_code=409, detail='fighter1_id and fighter2_id must be different')
    if stats1.fighter_id != fight.fighter1_id:
        raise HTTPException(status_code=400, detail='fighter1_id must correspond with fighter_id given in stats1')
    if stats2.fighter_id != fight.fighter2_id:
        raise HTTPException(status_code=400, detail='fighter2_id must correspond with fighter_id given in stats2')
    
    # round_time should be less than equal to 5:00
    try:
        round_time = datetime.strptime(fight.round_time, '%M:%S')
    except ValueError:
        raise HTTPException(status_code=400, detail='round_time not in M:S format')
    seconds = (timedelta(minutes=5, seconds=0) - timedelta(minutes=round_time.minute, seconds=round_time.second)).seconds
    if seconds > 300:
        raise HTTPException(status_code=400, detail='given round_time too large')

    if fight.result != None:
        if fight.result != fight.fighter1_id and fight.result != fight.fighter2_id:
            raise HTTPException(status_code=400, detail='result must be null or either the id of one of the fighters')
    
    with db.engine.begin() as conn:
        check = conn.execute(
            sqlalchemy.select(db.events.c.event_id).
            where(db.events.c.event_id == fight.event_id)
        ).fetchall()
        if not check:
            raise HTTPException(status_code=404, detail='event not found')

        check = conn.execute(
            sqlalchemy.select(db.fighters.c.fighter_id).
            where((db.fighters.c.fighter_id == stats2.fighter_id)
                  | (db.fighters.c.fighter_id == stats1.fighter_id))
        ).fetchall()
        if len(check) != 2:
            raise HTTPException(status_code=404, detail='a given fighter_id was not found')
        
        result = conn.execute(
            sqlalchemy.insert(db.fighter_stats).
            values(kd=stats1.kd, strikes=stats1.strikes, td=stats1.td,
                   sub=stats1.sub, fighter_id=stats1.fighter_id)
        )
        stats1_id = result.inserted_primary_key[0]

        result = conn.execute(
            sqlalchemy.insert(db.fighter_stats).
            values(kd=stats2.kd, strikes=stats2.strikes, td=stats2.td,
                   sub=stats2.sub, fighter_id=stats2.fighter_id)
        )
        stats2_id = result.inserted_primary_key[0]

        result = conn.execute(
            sqlalchemy.insert(db.fights).
            values(
                event_id = fight.event_id,
                fighter1_id = fight.fighter1_id,
                fighter2_id = fight.fighter2_id,
                round_num = fight.round_num,
                round_time = fight.round_time,
                result = fight.result,
                method_of_vic = fight.method_of_vic,
                weight_class = fight.weight_class,
                stats1_id = stats1_id,
                stats2_id = stats2_id,
            )
        )

    return {'fight_id': result.inserted_primary_key[0]}
