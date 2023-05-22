import os
import sqlalchemy
from sqlalchemy import create_engine
import dotenv

# DO NOT CHANGE THIS TO BE HARDCODED. ONLY PULL FROM ENVIRONMENT VARIABLES.
def database_connection_url():
    dotenv.load_dotenv()
    DB_USER: str = os.environ.get("POSTGRES_USER")
    DB_PASSWD = os.environ.get("POSTGRES_PASSWORD")
    DB_SERVER: str = os.environ.get("POSTGRES_SERVER")
    DB_PORT: str = os.environ.get("POSTGRES_PORT")
    DB_NAME: str = os.environ.get("POSTGRES_DB")
    return f"postgresql://{DB_USER}:{DB_PASSWD}@{DB_SERVER}:{DB_PORT}/{DB_NAME}"

# Create a new DB engine based on our connection string
engine = create_engine(database_connection_url())

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata_obj = sqlalchemy.MetaData(naming_convention=convention)
fighters = sqlalchemy.Table("fighters", metadata_obj, autoload_with=engine)
fights = sqlalchemy.Table("fights", metadata_obj, autoload_with=engine)
events = sqlalchemy.Table("events", metadata_obj, autoload_with=engine)
fighter_stats = sqlalchemy.Table("fighter_stats", metadata_obj, autoload_with=engine)
events = sqlalchemy.Table("events", metadata_obj, autoload_with=engine)
stances = sqlalchemy.Table("stances", metadata_obj, autoload_with=engine)
victory_methods = sqlalchemy.Table("victory_methods", metadata_obj, autoload_with=engine)
