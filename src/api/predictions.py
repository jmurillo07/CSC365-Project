from fastapi import APIRouter, HTTPException
from enum import Enum
from fastapi.params import Query
from src import database as db
from pydantic import BaseModel, Field
from typing import List
from src.api.users import UserJson, authenticate_user
from datetime import datetime
import sqlalchemy


class PredictionJson(BaseModel):
    fight_id: int
    fighter_id: int


router = APIRouter()


@router.get("/predictions/count", tags=["predictions"])
def get_prediction(fight_id: int):
    """
    This endpoint takes in a `fight_id` and returns how many predictions each
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
        SELECT fighter_id, fighter1_id, fighter2_id, COUNT(*) AS ct
        FROM predictions
            INNER JOIN fights ON predictions.fight_id = fights.fight_id
        WHERE predictions.fight_id = (:fight_id)
        GROUP BY fighter_id, fighter1_id, fighter2_id
        """
    )

    names = sqlalchemy.text(
        """
        SELECT fighter1_id, fighter2_id, result,
            fighter_id, CONCAT(first_name, ' ', last_name) AS name,
            method_of_vic
        FROM fights
	        INNER JOIN fighters ON fighter1_id = fighter_id OR fighter2_id = fighter_id
        WHERE fight_id = (:fight_id);
        """
    )

    with db.engine.connect() as conn:
        result = conn.execute(predictions, [{"fight_id": fight_id}])
        count = result.fetchall()
        if count is None:
            raise HTTPException(status_code=404, detail='fight does not exist')
        count_1 = 0
        count_2 = 0
        for row in count:
            if row.fighter_id == row.fighter1_id:
                count_1 = row.ct
            if row.fighter_id == row.fighter2_id:
                count_2 = row.ct
        
        result = conn.execute(names, [{"fight_id": fight_id}])
        names = result.fetchall()
        fight_result = None
        method = None
        f1_id = None

        for row in names:
            if row.fighter_id == row.fighter1_id:
                name_1 = row.name
                f1_id = row.fighter1_id
            if row.fighter_id == row.fighter2_id:
                name_2 = row.name
            fight_result = row.result
            method = row.method_of_vic
        
        if fight_result is None and method is None:
            final_result = "Unknown"  # Probably overturned
        elif fight_result is None:
            final_result = "Draw"
        elif fight_result == f1_id:
            final_result = name_1
        else:
            final_result = name_2

        json = {
            "fighter1": name_1,
            "fighter1_count": count_1,
            "fighter2": name_2,
            "fighter2_count": count_2,
            "result": final_result,
        }
    
    return json


@router.post("/predictions/add/", tags=["predictions"])
def add_prediction(user: UserJson, prediction: PredictionJson):
    """
    This endpoint takes in a user model, requiring their name and password, and
    a prediction model, requiring the `fight_id`, the `fighter_id` and the result
    they believe will happen.

    Returns the count for the prediction for the fight.

    If the user's account fails authentication (nonexistant/invalid password), then
    the end point will reject the prediction.
    The result should be the fighter_id of the fighter they believe will win the
    fight. A user is not allowed to predict a fight will end in a draw.
    Additionally, this endpoint ensures that the prediction is made at most one
    day before the `event_date` of the event the `fight_id` is associated with.
    """
    result = authenticate_user(user)
    if result['status'] == 'failed':
        raise HTTPException(status_code=401, detail='invalid password, try again.')

    fight_info = sqlalchemy.text(
        """
        SELECT fight_id, fighter1_id, fighter2_id, event_date
        FROM fights
            INNER JOIN events ON fights.event_id = events.event_id
        WHERE fight_id = (:fight_id) AND (fighter1_id = (:fighter_id)
                                          OR fighter2_id = (:fighter_id))
        """
    )

    with db.engine.begin() as conn:
        result = conn.execute(fight_info, [{"fight_id": prediction.fight_id,
                                            "fighter_id": prediction.fighter_id}]).first()
        if result is None:
            raise HTTPException(status_code=400,
                                detail="given bad fight_id or fighter_id")
        
        if (result.event_date - datetime.now()).days < 1:
            raise HTTPException(status_code=400,
                                detail="too late to submit prediction for this fight")
        
        # Get user_id
        result = conn.execute(
            sqlalchemy.select(db.users.c.user_id)
            .where(db.users.c.username == user.username)
        ).first()

        conn.execute(
            sqlalchemy.insert(db.predictions)
            .values(fight_id=prediction.fight_id,
                    fighter_id=prediction.fighter_id,
                    user_id=result.user_id)
        )
    
    return get_prediction(prediction.fight_id)