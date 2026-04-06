from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

MY_ENGINE = create_engine(
    f'postgresql://{settings.DB_USERNAME}:{settings.DB_PASSWORD}@{settings.DB_SERVER}:{settings.DB_PORT}/{settings.DB_NAME}',
    echo=False)
SESSION = sessionmaker(bind=MY_ENGINE)

Base = declarative_base()

# FastAPI Dependency for injecting the DB session
def get_db_session():
    current_session = SESSION()
    try:
        yield current_session  # give the db session to the requested point
    finally:
        # shut the session at the end of the task
        current_session.commit()
        current_session.close()
