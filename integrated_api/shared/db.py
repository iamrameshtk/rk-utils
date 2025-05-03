# shared/db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

def get_db_url(db_name):
    """Generate database URL from environment variables"""
    # Get database connection parameters from environment variables
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_USER = os.getenv("DB_USER", "username")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
    
    # Construct the database URL
    return f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{db_name}"

def get_session_maker(db_name):
    """Create and return a session maker and engine for the given database name"""
    database_url = get_db_url(db_name)
    engine = create_engine(database_url)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine), engine
