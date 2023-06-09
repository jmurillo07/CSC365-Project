from faker import Faker
import random
import sqlalchemy
from sqlalchemy.sql import text
from src import database as db

fake = Faker()

# requires empty db to run

numVenues = 600
numEvents = 2500  # (remember has fkey with venues)
numFights = 200000  # (remember has fkey with events, fights, fighter_stats)
numFighter_stats = 400000  # (remember has fkey with fighters)
numFighters = 800000
numUsers = 20000
numPredictions = 300000  # (remember has fkey with fights and users, fights and users has to be unique now)

# make sure connection is made to local DB, change from database.py
engine = sqlalchemy.create_engine(db.database_connection_url())

# for reference

stances = [
    {'stance': 'Orthodox'},
    {'stance': 'Southpaw'},
    {'stance': 'Switch'},
]   
victory_methods = [
    {'method': 'SUB'},
    {'method': 'KO/TKO'},
    {'method': 'S-Dec'},
    {'method': 'M-Dec'},
    {'method': 'U-Dec'},
    {'method': 'CNC'},
    {'method': 'DQ'},
]
weight_classes = [
    {'class': 'Flyweight'},
    {'class': 'Bantamweight'},
    {'class': 'Featherweight'},
    {'class': 'Lightweight'},
    {'class': 'Welterweight'},
    {'class': 'Middleweight'},
    {'class': 'Light Heavyweight'},
    {'class': 'Heavyweight'},
    {'class': "Women's Strawweight"},
    {'class': "Women's Flyweight"},
    {'class': "Women's Bantamweight"},
    {'class': "Women's Featherweight"},
    {'class': 'Catch Weight'},
    {'class': 'Open Weight'}
]

with engine.begin() as conn:
    fighters = []
    for _ in range(numFighters):
        first_name = fake.first_name()
        last_name = fake.last_name()
        height = random.randint(1, 9999)
        reach = random.randint(1, 9999)
        stance_id = random.choice([1, 2, 3])

        fighters.append({
            'first_name': first_name,
            'last_name': last_name,
            'height': height,
            'reach': reach,
            'stance_id': stance_id
        })
    conn.execute(db.fighters.insert(), fighters)

    fighter_stats = []
    for fighter_id in range(1, numFighters + 1):
        kd = random.randint(0, 10)
        strikes = random.randint(0, 1000)
        td = random.randint(0, 100)
        sub = random.randint(0, 20)

        fighter_stats.append({
            'stats_id': fighter_id,
            'kd': kd,
            'strikes': strikes,
            'td': td,
            'sub': sub,
            'fighter_id': fighter_id
        })
    conn.execute(db.fighter_stats.insert(), fighter_stats)

    venues = []
    for venue_id in range(1, numVenues + 1):
        venue_name = fake.company()

        venues.append({
            'venue_id': venue_id,
            'venue_name': venue_name
        })
    conn.execute(db.venue.insert(), venues)

    events = []
    for event_id in range(1, numEvents + 1):
        event_name = fake.catch_phrase()
        event_date = fake.date_this_decade()
        venue_id = random.randint(1, numVenues)
        attendance = random.randint(100, 10000)

        events.append({
            'event_id': event_id,
            'event_name': event_name,
            'event_date': event_date,
            'venue_id': venue_id,
            'attendance': attendance
        })
    conn.execute(db.events.insert(), events)

    fights = []
    for fight_id in range(1, numFights + 1):
        event_id = random.randint(1, numEvents)
        result = random.randint(0, 1)
        fighter1_id = random.randint(1, numFighters)
        fighter2_id = random.randint(1, numFighters)
        weight_class = random.randint(1, len(weight_classes))
        method_of_vic = random.randint(1, len(victory_methods))
        round_num = random.randint(1, 5)
        round_time = fake.time()

        stats1_id = fighter1_id
        stats2_id = fighter2_id

        fights.append({
            'fight_id': fight_id,
            'event_id': event_id,
            'result': result,
            'fighter1_id': fighter1_id,
            'fighter2_id': fighter2_id,
            'weight_class': weight_class,
            'method_of_vic': method_of_vic,
            'round_num': round_num,
            'round_time': round_time,
            'stats1_id': stats1_id,
            'stats2_id': stats2_id
        })
    conn.execute(db.fights.insert(), fights)

    users = []
    for user_id in range(1, numUsers + 1):
        username = fake.user_name()
        password = fake.password()

        users.append({
            'user_id': user_id,
            'username': username,
            'password': password
        })
    conn.execute(db.users.insert(), users)

    predictions = []
    for prediction_id in range(1, numPredictions + 1):
        fight_id = random.randint(1, numFights)
        fighter_id = random.randint(1, numFighters)
        user_id = random.randint(1, numUsers)

        predictions.append({
            'prediction_id': prediction_id,
            'fight_id': fight_id,
            'fighter_id': fighter_id,
            'user_id': user_id
        })
    conn.execute(db.predictions.insert(), predictions)
