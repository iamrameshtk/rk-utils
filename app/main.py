# main.py
import logging
import os
from datetime import datetime
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
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

# Get database connection from environment variables
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://username:password@localhost:5432/sonarqube_db"
)

# Create SQLAlchemy engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define database model
class SonarQubeReport(Base):
    __tablename__ = "sonarqube_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False)
    repository_key = Column(String, nullable=False, index=True)
    code_smells = Column(Integer, nullable=False)
    technical_debt_minutes = Column(Integer, nullable=False)
    security_hotspots = Column(Integer, nullable=False)
    security_rating = Column(Float, nullable=False)

# Create tables in the database if they don't exist
Base.metadata.create_all(bind=engine)

# Pydantic model for response
class SonarQubeReportResponse(BaseModel):
    timestamp: datetime
    repository_key: str
    code_smells: int
    technical_debt_minutes: int
    security_hotspots: int
    security_rating: float
    
    class Config:
        from_attributes = True

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize FastAPI app
app = FastAPI(title="SonarQube Report API")

@app.get("/", response_model=List[SonarQubeReportResponse])
async def read_reports(
    repository_key: Optional[str] = Query(None, description="Filter by repository key"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Fetching reports with filter: repository_key={repository_key}, limit={limit}, skip={skip}")
        
        query = db.query(SonarQubeReport)
        
        if repository_key:
            query = query.filter(SonarQubeReport.repository_key == repository_key)
        
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
async def health_check():
    try:
        # Simple health check - verify database connection
        with SessionLocal() as db:
            db.execute("SELECT 1")
        return {"status": "healthy"}
    
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=503, detail="Service unhealthy")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)