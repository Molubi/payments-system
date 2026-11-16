import time
from sqlalchemy.exc import OperationalError
from app.database import engine


def wait_for_db():
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

    raise Exception("Database never became available.")
