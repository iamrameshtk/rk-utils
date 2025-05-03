# app/sonarqube/main.py
import os
from datetime import datetime
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy import Column, String, Float, DateTime, Integer, PrimaryKeyConstraint, Text, desc, or_
from sqlalchemy.orm import Session

from shared.db import Base, get_session_maker
from shared.logging import setup_logger

# Set up logger
logger = setup_logger("sonarqube_api")

# Get session maker for SonarQube DB
DB_NAME = os.getenv("SONARQUBE_DB_NAME", "sonarqube_db")
SessionLocal, engine = get_session_maker(DB_NAME)

# Define database model with the specified datatypes
class SonarQubeReport(Base):
    __tablename__ = "sonarqube_reports"
    
    # Schema columns with correct datatypes
    timestamp = Column(DateTime, nullable=False)
    repository_key = Column(Text, nullable=False, index=True)
    code_smells = Column(Integer, nullable=False)
    technical_debt_minutes = Column(Float, nullable=False)
    security_hotspots = Column(Integer, nullable=False)
    security_rating = Column(Integer, nullable=False)
    team = Column(Text, nullable=True, index=True)  # Added index for faster team filtering
    
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
    team: Optional[str] = None
    
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
    team: Optional[str] = Query(None, description="Filter by team name (e.g. Team-A, Team-B, Team-C)"),
    sort_order: str = Query("desc", description="Sort order for timestamp (asc or desc)"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Fetching reports with filters: repository_key={repository_key}, team={team}, sort_order={sort_order}, limit={limit}, skip={skip}")
        
        query = db.query(SonarQubeReport)
        
        # Apply repository_key filter if provided
        if repository_key:
            query = query.filter(SonarQubeReport.repository_key == repository_key)
        
        # Apply team filter if provided, with flexible matching
        if team:
            # Try different possible formats of team names in the database
            team_filters = []
            
            # 1. Exact match (e.g., "Team-A")
            team_filters.append(SonarQubeReport.team == team)
            
            # 2. Match with surrounding quotes (e.g., "\"Team-A\"")
            team_filters.append(SonarQubeReport.team == f'"{team}"')
            
            # 3. Match with trimmed spaces
            team_filters.append(SonarQubeReport.team == team.strip())
            
            # 4. Case insensitive match
            team_filters.append(SonarQubeReport.team.ilike(team))
            
            # Combine all filters with OR
            query = query.filter(or_(*team_filters))
            
            # Log the team filter being applied
            logger.info(f"Applied team filter with variations of '{team}'")
        
        # Apply sorting by timestamp
        if sort_order.lower() == "asc":
            query = query.order_by(SonarQubeReport.timestamp)
        else:
            query = query.order_by(desc(SonarQubeReport.timestamp))
        
        # Log the SQL query for debugging (comment out in production)
        sql_str = str(query.statement.compile(dialect=engine.dialect, compile_kwargs={"literal_binds": True}))
        logger.debug(f"SQL Query: {sql_str}")
        
        # Apply pagination
        reports = query.offset(skip).limit(limit).all()
        
        if not reports:
            logger.warning(f"No reports found for the given filters: repository_key={repository_key}, team={team}")
            return []
        
        logger.info(f"Successfully fetched {len(reports)} reports")
        return reports
    
    except Exception as e:
        logger.error(f"Error fetching reports: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/teams", response_model=List[str])
def get_teams(db: Session = Depends(get_db)):
    """Get a list of all unique team names in the database"""
    try:
        # Query distinct team values
        teams_query = db.query(SonarQubeReport.team).distinct().filter(SonarQubeReport.team.isnot(None))
        teams = [team[0] for team in teams_query.all()]
        
        logger.info(f"Successfully fetched {len(teams)} unique team names")
        return teams
    
    except Exception as e:
        logger.error(f"Error fetching teams: {str(e)}", exc_info=True)
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
            "/reports": "Get SonarQube reports with filtering by repository_key, team and sorting by timestamp",
            "/teams": "Get a list of all unique team names in the database",
            "/health": "Check API health status"
        }
    }

if __name__ == "__main__":
    # This will only be used when running the file directly, not when mounted in server.py
    uvicorn.run("app.sonarqube.main:app", host="0.0.0.0", port=8000, reload=True)