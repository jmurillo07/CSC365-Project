from fastapi import APIRouter, HTTPException
from enum import Enum
from fastapi.params import Query
from src import database as db
from pydantic import BaseModel, Field
from typing import List
import sqlalchemy


class PredictionJson(BaseModel):
    fight_id: int
    fighter_id: int
    user_id: int

router = APIRouter()


@router.get("/predictions/count", tags=["predictions"])
def get_predictions(fight_id: int):
    """
    This endpoint takes in a fight_id and returns how many predictions each
    fighter got from the fight.

    Returns a dictionary with keys:
    * `fighter1`: The name of fighter 1.
    * `fighter1_count`: The number of predictions which chose fighter 1 to win the fight.
    * `fighter2`: The name of fighter 2.
    * `fighter2_count`: The number of predictions which chose fighter 2 to win the fight.
    * `result`: The result of the fight. Either the name of the fighter who won, "Draw", or "Unknown".
    """
    predictions = sqlalchemy.text(
        """
        SELECT
            COUNT(*) FILTER(WHERE fighter_id = fights.fighter1_id) OVER (PARTITION BY fighter_id) AS for_1,
            COUNT(*) FILTER(WHERE fighter_id = fights.fighter2_id) OVER (PARTITION BY fighter_id) AS for_2
        FROM predictions
            INNER JOIN fights ON predictions.fight_id = fights.fight_id
        WHERE predictions.fight_id = (:fight_id)
        """
    )

    names = sqlalchemy.text(
        """
        SELECT fighter1_id, fighter2_id, result, CONCAT(first_name + ' ' + last_name)
        FROM fights
            INNER JOIN fights ON fighters.fighter_id = fights.fighter1_id
                    OR fighters.fighter_id = fights.fighter2_id
        WHERE fights.fight_id = (:fight_id)
        """
    )