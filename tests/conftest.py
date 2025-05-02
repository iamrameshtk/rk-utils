import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from datetime import datetime

from app.database import Base, get_db
from app.main import app
from app.models.sonarqube import SonarQubeReport

# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    # Create the database tables
    Base.metadata.create_all(bind=engine)
    
    # Create a session
    db = TestingSessionLocal()
    
    # Seed test data
    sample_reports = [
        SonarQubeReport(
            timestamp=datetime(2025, 4, 1, 10, 30),
            repository_key="project-a",
            code_smells=120,
            technical_debt_minutes=450.5,
            security_hotspots=8,
            security_rating="A"
        ),
        SonarQubeReport(
            timestamp=datetime(2025, 4, 2, 14, 15),
            repository_key="project-b",
            code_smells=85,
            technical_debt_minutes=310.2,
            security_hotspots=3,
            security_rating="B"
        ),
    ]
    db.add_all(sample_reports)
    db.commit()
    
    try:
        yield db
    finally:
        db.close()
        
        # Drop tables after test
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    # Override the get_db dependency
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    # Clear dependency override
    app.dependency_overrides.clear()