import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_USER = os.getenv("DB_USER", "username")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "sonarqube_db")

# Check environment to determine database connection
ENV = os.getenv("ENV", "development")

if ENV == "development":
    # Use SQLite for development to avoid PostgreSQL dependency issues
    DATABASE_URL = "sqlite:///./sonarqube.db"
else:
    # Use PostgreSQL in production
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# API settings
API_TITLE = "SonarQube Analysis API"
API_DESCRIPTION = "API for retrieving SonarQube static analysis reports"
API_VERSION = "1.0.0"