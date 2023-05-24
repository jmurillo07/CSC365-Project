from fastapi import APIRouter, HTTPException
from src import database as db
from pydantic import BaseModel
import sqlalchemy


class UserJson(BaseModel):
    username: str
    password: str

router = APIRouter()


@router.get("/users/{id}", tags=["users"])
def get_user(id: int):
    """
    This endpoint takes in a user_id and returns the username of that user.
    If the user_id is not found, returns an error.
    """
    find = (sqlalchemy.select(db.users.c.username)).where(db.users.c.user_id == id)

    with db.engine.connect() as conn:
        result = conn.execute(find).first()
        if result is None:
            raise HTTPException(status_code=400, detail='user does not exist')

    return {'username': result[0]}


@router.get("/users/", tags=["users"])
def get_users(name: str = ""):
    """
    This endpoint takes in a username and returns every user_id and username where
    the username matches the name.
    """
    find = (sqlalchemy.select(db.users.c.user_id, db.users.c.username)).\
        where(db.users.c.username.ilike(f"%{name}%"))
    
    with db.engine.connect() as conn:
        result = conn.execute(find).fetchall()
        json = []
        for row in result:
            json.append(
                {
                    "user_id": row.user_id,
                    "username": row.username,
                }
            )
    
    return json


@router.post("/users/login", tags=["users"])
def authenticate_user(user: UserJson):
    """
    This endpoint takes in a usertype and verifies that the user exists
    and that the password given is correct for that user.

    If the user does not exist, raises an error.

    Returns a string indicating whether or not the password was correct.
    """
    verify = sqlalchemy.text(
        """
        SELECT user_id
        FROM users
        WHERE username = :username
            AND password = crypt(:password, password);
        """
    )

    check_exists = sqlalchemy.text(
        """
        SELECT username
        FROM users
        WHERE username = :username
        """
    )

    with db.engine.connect() as conn:
        result = conn.execute(check_exists, [{'username': user.username}]).first()
        if result is None:
            raise HTTPException(status_code=404, detail='user does not exist')

        result = conn.execute(verify, [{'username': user.username,
                                        'password': user.password}]).first()
        if result is None:
            return {'status': 'failed'}
    
    return {'status': 'success'}


@router.post("/users/create", tags=["users"])
def add_user(user: UserJson):
    """
    This endpoint takes in a user datatype and adds it to the database.
    Usernames are assured to be unique by the endpoint, if a username given
    is not unique it will return an error.

    On success this endpoint returns the id of the resulting user added to the database.
    """
    encryption = sqlalchemy.text(
        """
        INSERT INTO users (username, password) VALUES (
            :username,
            crypt(:password, gen_salt('bf'))
        )
        RETURNING user_id
        """
    )

    check_unique = sqlalchemy.text(
        """
        SELECT username
        FROM users
        WHERE username = :username
        """
    )

    with db.engine.connect() as conn:
        check = conn.execute(check_unique, [{'username': user.username}])
        if check.first() is not None:
            raise HTTPException(status_code=409, detail='username already taken')
        result = conn.execute(encryption, [{'username': user.username, 'password': user.password}])
        conn.commit()
    
    return {"user_id": result.first()[0]}
