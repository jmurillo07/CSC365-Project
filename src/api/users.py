from fastapi import APIRouter, HTTPException
from src import database as db
from typing import Optional
from pydantic import BaseModel, Field
import sqlalchemy


class UserJson(BaseModel):
    username: str
    password: str


class UserUpdateNameJson(BaseModel):
    old_username: str
    password: str
    new_username: str


class UserUpdatePasswordJson(BaseModel):
    username: str
    old_password: str
    new_password: str

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


@router.get("/users", tags=["users"])
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
    This endpoint takes in a user datatype and verifies that the user exists
    and that the password given is correct for that user.

    If the user does not exist, raises an error.

    Upon success returns the `user_id` of the authenticated user.
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
            raise HTTPException(status_code=401, detail='invalid password, try again.')
    
    return {'user_id': result.user_id}


@router.post("/users", tags=["users"])
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
    
    return {'user_id': result.inserted_primary_key[0]}


@router.post("/users/delete", tags=["users"])
def delete_user(user: UserJson):
    """
    This endpoint takes in a user datatype, verifies that the user exists, authenticates
    the user, then deletes all known predictions associated with the user and
    finally the user itself.

    Throws an error when the user does not exist or fails authentication.
    """
    result = authenticate_user(user)  # will raise errors if user doesnt exist/password is wrong
    
    delete = (
        sqlalchemy.delete(db.users).
        where(db.users.c.user_id == result['user_id'])
    )

    with db.engine.begin() as conn:
        result = conn.execute(delete)
    
        if result.rowcount > 0:
            return {'result': 'delete successful'}
        else:
            conn.rollback()
            raise HTTPException(status_code=500, detail='delete went wrong, action rolled back')


@router.put("/users/update/name", tags=["users"])
def update_username(user: UserUpdateNameJson):
    """
    This endpoint takes in a `username` and `password` and a new desired username.

    After authenticating the user, checks whether or not the
    desired username is available.

    If so, it will change the username. If the name is not available, it will refuse to
    change it.

    Returns success upon a successful update, errors otherwise.
    """
    user_model = UserJson(username=user.old_username, password=user.password)
    auth_result = authenticate_user(user_model)  # will raise errors if user doesnt exist/password is wrong

    with db.engine.begin() as conn:
        result = conn.execute(
            sqlalchemy.select(db.users.c.user_id).
            where(db.users.c.username == user.new_username)
        ).fetchall()
        if result:
            raise HTTPException(status_code=409, detail='name already in use')

        result = conn.execute(
            sqlalchemy.update(db.users).
            where(db.users.c.user_id == auth_result['user_id']).
            values(username=user.new_username)
        )

        if result.rowcount > 0:
            return {'result': 'update successful'}
        else:
            conn.rollback()
            raise HTTPException(status_code=500, detail='update went wrong, action rolled back')


@router.put("/users/update/password", tags=["users"])
def update_password(user: UserUpdatePasswordJson):
    """
    This endpoint takes in a `username` and `password` and a new desired password.

    If the user is authenticated, then the password will be changed.

    Returns success upon a successful update.
    Errors if the user doesn't exist or authentication fails.
    """
    user_model = UserJson(username=user.username, password=user.old_password)
    auth_result = authenticate_user(user_model)  # will raise errors if user doesnt exist/password is wrong

    update = sqlalchemy.text(
        """
        UPDATE users SET password = crypt(:password, gen_salt('bf'))
        WHERE users.user_id = (:user_id)
        """
    ).bindparams(
        sqlalchemy.bindparam('user_id', auth_result['user_id']),
        sqlalchemy.bindparam('password', user.new_password),
    )

    with db.engine.begin() as conn:
        result = conn.execute(update)

        if result.rowcount > 0:
            return {'result': 'update successful'}
        else:
            conn.rollback()
            raise HTTPException(status_code=500, detail='update went wrong, action rolled back')