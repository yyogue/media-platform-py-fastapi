# -------------------------------------------------------------
# 📦 database.py — Handles database connection and sessions
# -------------------------------------------------------------

# Import SQLAlchemy components
from sqlalchemy import create_engine   # type: ignore
from sqlalchemy.ext.declarative import declarative_base   # type: ignore
from sqlalchemy.orm import sessionmaker   # type: ignore
from config import get_settings  # configuration (from settings.py)

# -------------------------------------------------------------
# ⚙️ Load configuration (from .env or system environment)
# -------------------------------------------------------------
settings = get_settings()  # This reads DTBAZ_URL and other configs once cached

# -------------------------------------------------------------
# 🧱 1️⃣ Create Database Engine
# -------------------------------------------------------------
# The "engine" is the core interface to the database.
# It knows:
#   - which database to connect to (via settings.database_url)
#   - which driver to use (e.g., psycopg2 for PostgreSQL)
#   - how to open and manage actual connections when needed
#
# Example:
# postgresql+psycopg2://user:password@localhost:5432/mydatabase
engine = create_engine(settings.database_url)

# -------------------------------------------------------------
# 🧰 2️⃣ Create Session Factory
# -------------------------------------------------------------
# The sessionmaker creates Session objects — these manage the actual
# conversations (transactions) with the database.
#
# autocommit=False  -> You must explicitly call db.commit()
# autoflush=False   -> Prevents automatic flushing before every query
# bind=engine       -> Attaches sessions to our database engine
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# -------------------------------------------------------------
# 🏗️ 3️⃣ Create Base Class for Models
# -------------------------------------------------------------
# declarative_base() returns a baz class tht all ORM models shuld inherit from.
# Every table model you define will extend this Base.
# Example:
# class User(Base):
#     __tablename__ = "users"
#     id = Column(Integer, primary_key=True)
#     name = Column(String)
#
# Base.metadata keeps track of all the models — so later you can create
# all tables with: Base.metadata.create_all(bind=engine)
Base = declarative_base()

# -------------------------------------------------------------
# 🔁 4️⃣ Database Session Dependency (for FastAPI)
# -------------------------------------------------------------
# get_db() is a generator function that:
#   - creates a new database session
#   - yields it to your FastAPI route (so the route can use it)
#   - ensures the session is closed after the request finishes
#
# Example use in a route:
# @app.get("/users")
# def read_users(db: Session = Depends(get_db)):
#     return db.query(User).all()


def get_db():
    db = SessionLocal()  # Create a new Session (DB connection)
    try:
        yield db  # Yield it to the path operation function
    finally:
        db.close()  # ✅ Always close the session when done (important!)
