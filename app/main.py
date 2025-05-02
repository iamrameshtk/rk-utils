# main.py
import logging
import os
from datetime import datetime
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer, PrimaryKeyConstraint, Text, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("api.log")
    ]
)
logger = logging.getLogger(__name__)

# Get database connection parameters from environment variables
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "username")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_NAME = os.getenv("DB_NAME", "sonarqube_db")

# Construct the database URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Log database connection (without password)
logger.info(f"Connecting to database at {DB_HOST}:{DB_PORT}/{DB_NAME} as {DB_USER}")

# Create SQLAlchemy engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define database model with the specified datatypes
class SonarQubeReport(Base):
    __tablename__ = "sonarqube_reports"
    
    # Keep only the required schema columns with correct datatypes
    timestamp = Column(DateTime, nullable=False)
    repository_key = Column(Text, nullable=False, index=True)
    code_smells = Column(Integer, nullable=False)
    technical_debt_minutes = Column(Float, nullable=False)
    security_hotspots = Column(Integer, nullable=False)
    security_rating = Column(Integer, nullable=False)
    
    # Use a composite primary key
    __table_args__ = (
        PrimaryKeyConstraint('timestamp', 'repository_key'),
    )

# Create tables in the database if they don't exist
Base.metadata.create_all(bind=engine)

# Pydantic model for response
class SonarQubeReportResponse(BaseModel):
    timestamp: datetime
    repository_key: str
    code_smells: int
    technical_debt_minutes: float
    security_hotspots: int
    security_rating: int
    
    class Config:
        orm_mode = True

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize FastAPI app
app = FastAPI(title="SonarQube Report API")

@app.get("/reports", response_model=List[SonarQubeReportResponse])
def read_reports(
    repository_key: Optional[str] = Query(None, description="Filter by repository key"),
    sort_order: str = Query("desc", description="Sort order for timestamp (asc or desc)"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Fetching reports with filter: repository_key={repository_key}, sort_order={sort_order}, limit={limit}, skip={skip}")
        
        query = db.query(SonarQubeReport)
        
        # Apply repository_key filter if provided
        if repository_key:
            query = query.filter(SonarQubeReport.repository_key == repository_key)
        
        # Apply sorting by timestamp
        if sort_order.lower() == "asc":
            query = query.order_by(SonarQubeReport.timestamp)
        else:
            query = query.order_by(desc(SonarQubeReport.timestamp))
        
        # Apply pagination
        reports = query.offset(skip).limit(limit).all()
        
        if not reports:
            logger.warning(f"No reports found for the given filter: repository_key={repository_key}")
            return []
        
        logger.info(f"Successfully fetched {len(reports)} reports")
        return reports
    
    except Exception as e:
        logger.error(f"Error fetching reports: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health")
def health_check():
    try:
        # Simple health check - verify database connection
        with SessionLocal() as db:
            result = db.execute("SELECT 1").fetchone()
            if not result:
                raise Exception("Database query failed")
        return {"status": "healthy", "database": "connected"}
    
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.get("/")
def root():
    """Root endpoint to provide API information"""
    return {
        "name": "SonarQube Reports API",
        "version": "1.0.0",
        "endpoints": {
            "/reports": "Get SonarQube reports with filtering by repository_key and sorting by timestamp",
            "/health": "Check API health status"
        }
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)