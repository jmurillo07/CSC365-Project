""""
Convert data from the CSV files to the database.
Usage:
    1. In database.py comment out the Tables, leave the metadata object there.
    2. Run alembic downgrade base
    3. Run alembic upgrade base
    4. Uncomment out the Tables in database.py then run this file.
Only run this file once. If there is an error try to drop your tables (go through process again)
after fixing the error.
"""

import csv
import sqlalchemy as sa
import re
from datetime import datetime
from src import database as db

def try_parse(type, val):
    try:
        return type(val)
    except ValueError:
        return None

# Creates fighters
with open("ufc_fighters.csv", mode="r", encoding="utf-8") as csv_file:
    reader = csv.DictReader(csv_file, skipinitialspace=True)

    with db.engine.connect() as connection:
        for row in reader:
            f_name = try_parse(str, row['First Name'])
            l_name = try_parse(str, row['Last Name'])
            h = re.findall(r'\d+', try_parse(str, row['Height']))
            if h:
                h = int(h[0]) * 12 + int(h[1])
            else:
                h = None
            r = re.findall(r'\d+', try_parse(str, row['Reach']))
            if r:
                r = int(r[0])
            else:
                r = None
            s = try_parse(str, row['Stance'])
            match s:
                case 'Orthodox':
                    s = 1
                case 'Southpaw':
                    s = 2
                case 'Switch':
                    s = 3
                case _:
                    s = None
            
            connection.execute(
                sa.insert(db.fighters).
                values(first_name = f_name, last_name = l_name, height = h, reach = r, stance_id = s)
            )
        connection.commit()

# Creates events
with open("ufc_event_data.csv", mode="r", encoding="utf-8") as csv_file:
    reader = csv.DictReader(csv_file, skipinitialspace=True)
    old_name = None
    venue = 1  # Don't got the info for now.
    with db.engine.begin() as connection:
        connection.execute(
            sa.insert(db.venue).
            values(venue_id = venue)
        )
    with db.engine.connect() as connection:
        for row in reader:
            name = try_parse(str, row['Event Name'])
            if old_name != name:
                old_name = name
            else:
                continue
            date = datetime.date(datetime.strptime(try_parse(str, row['Event Date']), '%B %d, %Y'))
            attendance = None  # Also don't know atm

            connection.execute(
                sa.insert(db.events).
                values(event_name = name, event_date = date, venue_id = venue, attendance = attendance)
            )
        connection.commit()

# Creates fighter_stats and fights
with open("ufc_event_data.csv", mode="r", encoding="utf-8") as csv_file:
    reader = csv.DictReader(csv_file, skipinitialspace=True)
    with db.engine.connect() as connection:
        for row in reader:
            name = try_parse(str, row['Event Name'])
            fighter1 = try_parse(str, row['Fighter1'])
            fighter2 = try_parse(str, row['Fighter2'])
            result = try_parse(str, row['Result'])
            kd = try_parse(str, row['KD'])
            kd = re.findall(r'\d+', kd)
            if not kd:
                kd1 = None
                kd2 = None
            else:
                kd1 = int(kd[0])
                kd2 = int(kd[1])
            strikes = try_parse(str, row['Strikes'])
            strikes = re.findall(r'\d+', strikes)
            if not strikes:
                strikes1 = None
                strikes2 = None
            else:
                strikes1 = int(strikes[0])
                strikes2 = int(strikes[1])
            td = try_parse(str, row['TD'])
            td = re.findall(r'\d+', td)
            if not td:
                td1 = None
                td2 = None
            else:
                td1 = int(td[0])
                td2 = int(td[1])
            sub = try_parse(str, row['Sub'])
            sub = re.findall(r'\d+', sub)
            if not sub:
                sub1 = None
                sub2 = None
            else:
                sub1 = int(sub[0])
                sub2 = int(sub[1])
            weight_class = try_parse(str, row['Weight Class'])
            if "Women's Strawweight" in weight_class:
                weight_class = 9
            elif "Women's Flyweight" in weight_class:
                weight_class = 10
            elif "Women's Bantamweight" in weight_class:
                weight_class = 11
            elif "Women's Featherweight" in weight_class:
                weight_class = 12
            elif "Flyweight" in weight_class:
                weight_class = 1
            elif "Bantamweight" in weight_class:
                weight_class = 2
            elif "Featherweight" in weight_class:
                weight_class = 3
            elif "Lightweight" in weight_class:
                weight_class = 4
            elif "Welterweight" in weight_class:
                weight_class = 5
            elif "Middleweight" in weight_class:
                weight_class = 6
            elif "Light Heavyweight" in weight_class:
                weight_class = 7
            elif "Heavyweight" in weight_class:
                weight_class = 8
            elif "Catch Weight" in weight_class:
                weight_class = 13
            elif "Open Weight" in weight_class:
                weight_class = 14
            method = try_parse(str, row['Method'])
            if "SUB" in method:
                method = 1
            elif "KO/TKO" in method:
                method = 2
            elif "S-DEC" in method:
                method = 3
            elif "M-DEC" in method:
                method = 4
            elif "U-DEC" in method:
                method = 5
            elif "CNC" in method:
                method = 6
            elif "DQ" in method:
                method = 7
            else:
                method = None  # Overturned probably
            round = try_parse(int, row['Round'])
            time = try_parse(str, row['Time'])

            
            e_id = connection.execute(
                sa.select(db.events.c.event_id)
                .where(db.events.c.event_name == name)
            )
            e_id = e_id.first()[0]
            f1 = connection.execute(
                sa.text(
                    """
                    SELECT fighter_id
                    FROM fighters
                    WHERE (LOWER(first_name) LIKE LOWER(:fname)
                        AND LOWER(last_name) LIKE LOWER(:lname))
                        OR (LOWER(CONCAT(first_name, last_name)) LIKE LOWER(CONCAT((:fname), (:lname))))
                        OR (LOWER(CONCAT(first_name, ' ', last_name)) LIKE LOWER(CONCAT((:fname), ' ', (:lname))));
                    """
                ),[{"fname": fighter1.split()[0], "lname": " ".join(fighter1.split()[1:])}]
            )
            f1 = f1.first()
            if f1 is None:
                print(fighter1, fighter1.split()[0], " ".join(fighter1.split()[1:]))
                break
            else:
                f1 = f1[0]
            f2 = connection.execute(
                sa.text(
                    """
                    SELECT fighter_id
                    FROM fighters
                    WHERE (LOWER(first_name) LIKE LOWER(:fname)
                        AND LOWER(last_name) LIKE LOWER(:lname))
                        OR (LOWER(CONCAT(first_name, last_name)) LIKE LOWER(CONCAT((:fname), (:lname))))
                        OR (LOWER(CONCAT(first_name, ' ', last_name)) LIKE LOWER(CONCAT((:fname), ' ', (:lname))));
                    """
                ),[{"fname": fighter2.split()[0], "lname": " ".join(fighter2.split()[1:])}]
            )
            f2 = f2.first()
            if f2 is None:
                print(fighter2, fighter2.split()[0], " ".join(fighter2.split()[1:]))
                break
            else:
                f2 = f2[0]
            if result in fighter1:
                result = f1
            elif result in fighter2:
                result = f2
            else:
                result = None  # Draw or unknown
            stats1 = connection.execute(
                sa.insert(db.fighter_stats)
                .values(kd = kd1, strikes = strikes1,
                        td = td1, sub = sub1,
                        fighter_id = f1)
            )
            stats1 = stats1.inserted_primary_key[0]
            stats2 = connection.execute(
                sa.insert(db.fighter_stats)
                .values(kd = kd2, strikes = strikes2,
                        td = td2, sub = sub2,
                        fighter_id = f2)
            )
            stats2 = stats2.inserted_primary_key[0]
            fight = connection.execute(
                sa.insert(db.fights)
                .values(event_id = e_id, result = result, fighter1_id = f1,
                         fighter2_id = f2, weight_class = weight_class, method_of_vic = method, 
                         round_num = round, round_time = time, stats1_id = stats1, stats2_id = stats2)
            )
        
        connection.commit()
