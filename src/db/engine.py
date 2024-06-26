import os
from dotenv import load_dotenv

# DB API
from sqlalchemy import create_engine as alch_create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy_utils import database_exists, create_database

from src.db.queries import register_queries

load_dotenv()


def create_engine():
    return alch_create_engine(os.environ['DB_CONNECTION_STRING'],  # echo=True,
                          future=True)


engine = create_engine()

with engine.connect() as connection:
    for query in register_queries:
        connection.execute(query)
    connection.commit()

Session = sessionmaker(engine)
if not database_exists(engine.url):
    create_database(engine.url)
BaseModel = declarative_base()
