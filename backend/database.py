from sqlmodel import SQLModel, create_engine, Session
import os

# Render/Cloud uses DATABASE_URL. Local uses SQLite.
database_url = os.environ.get("DATABASE_URL")

if database_url and database_url.startswith("postgres://"):
    # SQLAlchemy requires postgresql://
    database_url = database_url.replace("postgres://", "postgresql://", 1)

if not database_url:
    sqlite_file_name = "inventory.db"
    database_url = f"sqlite:///{sqlite_file_name}"
    connect_args = {"check_same_thread": False}
    engine = create_engine(database_url, echo=True, connect_args=connect_args)
else:
    # PostgreSQL configuration
    engine = create_engine(database_url, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
