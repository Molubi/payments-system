import time
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

DATABASE_URL = (
    "postgresql+psycopg2://postgres:postgres@db:5432/payments"
)


def wait_for_db():

    engine = create_engine(DATABASE_URL)

    retries = 30

    while retries:

        try:
            connection = engine.connect()
            connection.close()

            print("Database is ready.")

            return

        except OperationalError:

            print("Waiting for database...")

            retries -= 1

            time.sleep(2)

    raise Exception(
        "Database never became available."
    )