from fastapi import FastAPI
from src.api import fighters

description = """
UFC API returns fighter and fight statistics from numbered events.

## Fighters

You can:
* **list fighters with sorting and filtering options.**
* **retrieve a specific fight by id**
* **add a new fighter to the database**

## Fights   

You can:

* **add a new fight to the database**
* **retrieve a specific fight by id**
* **add a community prediction to a fight**
* **retrieve a specific prediction by fight id**

## Events

You can:
* **retrieve a specific event by id**
* **add a new event by id**
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
        "description": "Access infromation on events.",
    },
]

app = FastAPI(
    title="UFC",
    description=description,
    version="0.0.1",
    openapi_tags=tags_metadata,
)
app.include_router(fighters.router)

@app.get("/")
async def root():
    return {"message": "Welcome to the UFC API. See /docs for more information."}
