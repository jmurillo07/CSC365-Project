from fastapi import FastAPI

from src.api import fights
from src.api import fighters
from src.api import users
from src.api import events
from src.api import predictions


description = """
Ultimate Fighting API returns fighter and fight statistics from numbered events.

## Fighters

You can:
* **list fighters with sorting and filtering options.**
* **retrieve a specific fight by id**
* **add a new fighter to the database**
* **update an existing fighter in the database**

## Fights   

You can:
* **retrieve a specific fight by id**
* **add a new fight to the database**
* **retrieve all fights under an event name**


## Events

You can:
* **retrieve a specific event by id**
* **retrieve all fights under an event name**
* **add a new event by id**


## Predictions

You can:
* **retrieve a specific prediction by fight id**
* **add your prediction to a fight**


## Users

You can:
* **retrieve a user's name by id**
* **list all username's matching a string**
* **authenticate a given username and password**
* **add a new user to the database**
* **delete an account**
* **update a username or password**
"""
tags_metadata = [
    {
        "name": "fighters",
        "description": "Access information on fighters.",
    },
    {
        "name": "fights",
        "description": "Access information on fights.",
    },
    {
        "name": "events",
        "description": "Access information on events.",
    },
    {
        "name": "predictions",
        "description": "Access information on predictions.",
    },
    {
        "name": "users",
        "description": "Access information on users.",
    },
]

app = FastAPI(
    title="UFC",
    description=description,
    version="0.0.3",
    openapi_tags=tags_metadata,
)
app.include_router(fights.router)
app.include_router(events.router)
app.include_router(fighters.router)
app.include_router(users.router)
app.include_router(predictions.router)

@app.get("/")
async def root():
    return {"message": "Welcome to the Ultimate Fighting API. See /docs for more information."}
