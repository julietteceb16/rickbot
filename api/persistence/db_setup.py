# db_setup.py
import os
from dotenv import load_dotenv

load_dotenv()

from api.persistence.db import engine
from api.persistence.models import Base

def create_db_tables():
    """Crea las tablas de la base de datos."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

if __name__ == "__main__":
    create_db_tables()