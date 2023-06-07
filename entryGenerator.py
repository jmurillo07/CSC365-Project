from faker import Faker
import random
import sqlalchemy
from src import database as db

fake = Faker()
num_entries = 1000000000

# make sure connection is made to local DB, change from database.py
engine = sqlalchemy.create_engine(db.database_connection_url())

with engine.begin() as conn:
    for _ in range(num_entries):
        first_name = fake.first_name()
        last_name = fake.last_name()
        height = random.randint(1, 9999)
        reach = random.randint(1, 9999)
        stance_id = random.choice([1, 2, 3])

        # allowing for duplicates, inserting all faker entries into the fighters table
        conn.execute(
            sqlalchemy.insert(db.fighters)
            .values(first_name=first_name,
                    last_name=last_name,
                    height=height,
                    reach=reach,
                    stance_id=stance_id))


