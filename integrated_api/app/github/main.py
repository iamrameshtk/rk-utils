# app/github/main.py
import os
from datetime import datetime, timedelta
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy import Column, String, Float, DateTime, Integer, Text, desc, or_, func
from sqlalchemy.orm import Session

from shared.db import Base, get_session_maker
from shared.logging import setup_logger

# Set up logger
logger = setup_logger("github_api")

# Get session maker for GitHub DB
DB_NAME = os.getenv("GITHUB_DB_NAME", "github_db")
SessionLocal, engine = get_session_maker(DB_NAME)

# Define database model based on the provided schema
class GitHubData(Base):
    __tablename__ = "github_data"
    
    # Schema columns with correct datatypes
    id = Column(Integer, primary_key=True)
    username = Column(Text, nullable=False, index=True)
    org_name = Column(Text, nullable=False, index=True)
    repository_name = Column(Text, nullable=False, index=True)
    pull_request_link = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    total_commits = Column(Integer, nullable=False)
    passing_commits = Column(Integer, nullable=False)
    failing_commits = Column(Integer, nullable=False)
    changes_per_commit = Column(Float, nullable=False)
    approved_reviews_received = Column(Integer, nullable=False)
    changes_requested_reviews_received = Column(Integer, nullable=False)
    commented_reviews_received = Column(Integer, nullable=False)
    approved_reviews_given = Column(Integer, nullable=False)
    changes_requested_reviews_given = Column(Integer, nullable=False)
    commented_reviews_given = Column(Integer, nullable=False)
    total_reviews = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

# Create tables in the database if they don't exist
Base.metadata.create_all(bind=engine)

# Pydantic model for response
class GitHubDataResponse(BaseModel):
    id: int
    username: str
    org_name: str
    repository_name: str
    pull_request_link: str
    title: str
    total_commits: int
    passing_commits: int
    failing_commits: int
    changes_per_commit: float
    approved_reviews_received: int
    changes_requested_reviews_received: int
    commented_reviews_received: int
    approved_reviews_given: int
    changes_requested_reviews_given: int
    commented_reviews_given: int
    total_reviews: int
    created_at: datetime
    
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
app = FastAPI(title="GitHub Data API")

@app.get("/reports", response_model=List[GitHubDataResponse])
def read_reports(
    username: Optional[str] = Query(None, description="Filter by GitHub username"),
    org_name: Optional[str] = Query(None, description="Filter by organization name"),
    repository_name: Optional[str] = Query(None, description="Filter by repository name"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date (format: YYYY-MM-DD)"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date (format: YYYY-MM-DD)"),
    date_range: Optional[str] = Query(None, description="Predefined date range (today, yesterday, this_week, last_week, this_month, last_month, this_year, custom)"),
    sort_by: str = Query("created_at", description="Field to sort by (created_at, total_commits, total_reviews)"),
    sort_order: str = Query("desc", description="Sort order (asc or desc)"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Fetching reports with filters: username={username}, org_name={org_name}, repository_name={repository_name}, date_range={date_range}")
        
        query = db.query(GitHubData)
        
        # Apply filters if provided
        if username:
            query = query.filter(GitHubData.username == username)
        
        if org_name:
            query = query.filter(GitHubData.org_name == org_name)
        
        if repository_name:
            query = query.filter(GitHubData.repository_name == repository_name)
        
        # Apply date filters
        if date_range:
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            if date_range == "today":
                tomorrow = today + timedelta(days=1)
                query = query.filter(GitHubData.created_at >= today, GitHubData.created_at < tomorrow)
            
            elif date_range == "yesterday":
                yesterday = today - timedelta(days=1)
                query = query.filter(GitHubData.created_at >= yesterday, GitHubData.created_at < today)
            
            elif date_range == "this_week":
                # Get start of the week (Monday)
                start_of_week = today - timedelta(days=today.weekday())
                query = query.filter(GitHubData.created_at >= start_of_week)
            
            elif date_range == "last_week":
                # Get start of the last week and end of the last week
                start_of_this_week = today - timedelta(days=today.weekday())
                start_of_last_week = start_of_this_week - timedelta(days=7)
                query = query.filter(GitHubData.created_at >= start_of_last_week, GitHubData.created_at < start_of_this_week)
            
            elif date_range == "this_month":
                # Get start of the month
                start_of_month = today.replace(day=1)
                query = query.filter(GitHubData.created_at >= start_of_month)
            
            elif date_range == "last_month":
                # Get start of this month and last month
                start_of_this_month = today.replace(day=1)
                # Go back one month and get the first day
                if start_of_this_month.month == 1:
                    start_of_last_month = start_of_this_month.replace(year=start_of_this_month.year-1, month=12)
                else:
                    start_of_last_month = start_of_this_month.replace(month=start_of_this_month.month-1)
                
                query = query.filter(GitHubData.created_at >= start_of_last_month, GitHubData.created_at < start_of_this_month)
            
            elif date_range == "this_year":
                start_of_year = today.replace(month=1, day=1)
                query = query.filter(GitHubData.created_at >= start_of_year)
            
            # If custom range, the start_date and end_date parameters should be used
        
        # Apply explicit date range filters if provided (these override the predefined ranges)
        if start_date:
            query = query.filter(GitHubData.created_at >= start_date)
        
        if end_date:
            # Add one day to include the end date fully
            next_day = end_date + timedelta(days=1)
            query = query.filter(GitHubData.created_at < next_day)
        
        # Apply sorting
        if sort_by == "created_at":
            sort_field = GitHubData.created_at
        elif sort_by == "total_commits":
            sort_field = GitHubData.total_commits
        elif sort_by == "total_reviews":
            sort_field = GitHubData.total_reviews
        else:
            sort_field = GitHubData.created_at
        
        if sort_order.lower() == "asc":
            query = query.order_by(sort_field)
        else:
            query = query.order_by(desc(sort_field))
        
        # Log the SQL query for debugging (comment out in production)
        sql_str = str(query.statement.compile(dialect=engine.dialect, compile_kwargs={"literal_binds": True}))
        logger.debug(f"SQL Query: {sql_str}")
        
        # Apply pagination
        reports = query.offset(skip).limit(limit).all()
        
        if not reports:
            logger.warning(f"No reports found for the given filters")
            return []
        
        logger.info(f"Successfully fetched {len(reports)} reports")
        return reports
    
    except Exception as e:
        logger.error(f"Error fetching reports: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/teams", response_model=List[str])
def get_teams(db: Session = Depends(get_db)):
    """Get a list of all unique organization names in the database (equivalent to teams)"""
    try:
        # Query distinct organization values
        orgs_query = db.query(GitHubData.org_name).distinct()
        organizations = [org[0] for org in orgs_query.all()]
        
        logger.info(f"Successfully fetched {len(organizations)} unique team names")
        return organizations
    
    except Exception as e:
        logger.error(f"Error fetching teams: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/repositories", response_model=List[str])
def get_repositories(
    org_name: Optional[str] = Query(None, description="Filter by organization name"),
    db: Session = Depends(get_db)
):
    """Get a list of all unique repository names in the database"""
    try:
        # Query distinct repository values
        repos_query = db.query(GitHubData.repository_name).distinct()
        
        # Apply org filter if provided
        if org_name:
            repos_query = repos_query.filter(GitHubData.org_name == org_name)
        
        repositories = [repo[0] for repo in repos_query.all()]
        
        logger.info(f"Successfully fetched {len(repositories)} unique repository names")
        return repositories
    
    except Exception as e:
        logger.error(f"Error fetching repositories: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/users", response_model=List[str])
def get_users(
    org_name: Optional[str] = Query(None, description="Filter by organization name"),
    repository_name: Optional[str] = Query(None, description="Filter by repository name"),
    db: Session = Depends(get_db)
):
    """Get a list of all unique usernames in the database with optional filtering"""
    try:
        # Query distinct username values
        users_query = db.query(GitHubData.username).distinct()
        
        # Apply filters if provided
        if org_name:
            users_query = users_query.filter(GitHubData.org_name == org_name)
        
        if repository_name:
            users_query = users_query.filter(GitHubData.repository_name == repository_name)
        
        users = [user[0] for user in users_query.all()]
        
        logger.info(f"Successfully fetched {len(users)} unique usernames")
        return users
    
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}", exc_info=True)
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
        "name": "GitHub Data API",
        "version": "1.0.0",
        "endpoints": {
            "/reports": "Get GitHub pull request data with filtering by username, org_name, repository_name, date range and sorting",
            "/teams": "Get a list of all unique organization names (teams)",
            "/repositories": "Get a list of all unique repository names",
            "/users": "Get a list of all unique usernames with optional filtering",
            "/health": "Check API health status"
        }
    }

if __name__ == "__main__":
    # This will only be used when running the file directly, not when mounted in server.py
    uvicorn.run("app.github.main:app", host="0.0.0.0", port=8000, reload=True)