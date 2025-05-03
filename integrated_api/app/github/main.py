# app/github/main.py
import os
from datetime import datetime
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

# Pydantic model for summary stats
class RepositorySummary(BaseModel):
    repository_name: str
    pull_request_count: int
    total_commits: int
    passing_commits: int
    failing_commits: int
    avg_changes_per_commit: float
    
    class Config:
        orm_mode = True

# Pydantic model for user stats
class UserStats(BaseModel):
    username: str
    total_pull_requests: int
    total_commits: int
    passing_commits_ratio: float
    avg_changes_per_commit: float
    reviews_given: int
    reviews_received: int
    
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

@app.get("/pull-requests", response_model=List[GitHubDataResponse])
def read_pull_requests(
    username: Optional[str] = Query(None, description="Filter by GitHub username"),
    org_name: Optional[str] = Query(None, description="Filter by organization name"),
    repository_name: Optional[str] = Query(None, description="Filter by repository name"),
    sort_by: str = Query("created_at", description="Field to sort by (created_at, total_commits, total_reviews)"),
    sort_order: str = Query("desc", description="Sort order (asc or desc)"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Fetching pull requests with filters: username={username}, org_name={org_name}, repository_name={repository_name}")
        
        query = db.query(GitHubData)
        
        # Apply filters if provided
        if username:
            query = query.filter(GitHubData.username == username)
        
        if org_name:
            query = query.filter(GitHubData.org_name == org_name)
        
        if repository_name:
            query = query.filter(GitHubData.repository_name == repository_name)
        
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
        pull_requests = query.offset(skip).limit(limit).all()
        
        if not pull_requests:
            logger.warning(f"No pull requests found for the given filters")
            return []
        
        logger.info(f"Successfully fetched {len(pull_requests)} pull requests")
        return pull_requests
    
    except Exception as e:
        logger.error(f"Error fetching pull requests: {str(e)}", exc_info=True)
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

@app.get("/organizations", response_model=List[str])
def get_organizations(db: Session = Depends(get_db)):
    """Get a list of all unique organization names in the database"""
    try:
        # Query distinct organization values
        orgs_query = db.query(GitHubData.org_name).distinct()
        organizations = [org[0] for org in orgs_query.all()]
        
        logger.info(f"Successfully fetched {len(organizations)} unique organization names")
        return organizations
    
    except Exception as e:
        logger.error(f"Error fetching organizations: {str(e)}", exc_info=True)
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

@app.get("/repository-summary", response_model=List[RepositorySummary])
def get_repository_summary(
    org_name: Optional[str] = Query(None, description="Filter by organization name"),
    db: Session = Depends(get_db)
):
    """Get summary statistics for repositories"""
    try:
        # Create a subquery to group by repository_name
        query = db.query(
            GitHubData.repository_name,
            func.count(GitHubData.id).label("pull_request_count"),
            func.sum(GitHubData.total_commits).label("total_commits"),
            func.sum(GitHubData.passing_commits).label("passing_commits"),
            func.sum(GitHubData.failing_commits).label("failing_commits"),
            func.avg(GitHubData.changes_per_commit).label("avg_changes_per_commit")
        ).group_by(GitHubData.repository_name)
        
        # Apply org filter if provided
        if org_name:
            query = query.filter(GitHubData.org_name == org_name)
        
        # Execute the query
        results = query.all()
        
        # Convert query results to response model
        summary_list = []
        for row in results:
            summary = RepositorySummary(
                repository_name=row.repository_name,
                pull_request_count=row.pull_request_count,
                total_commits=row.total_commits,
                passing_commits=row.passing_commits,
                failing_commits=row.failing_commits,
                avg_changes_per_commit=row.avg_changes_per_commit
            )
            summary_list.append(summary)
        
        logger.info(f"Successfully generated summary for {len(summary_list)} repositories")
        return summary_list
    
    except Exception as e:
        logger.error(f"Error generating repository summary: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/user-stats", response_model=List[UserStats])
def get_user_stats(
    org_name: Optional[str] = Query(None, description="Filter by organization name"),
    repository_name: Optional[str] = Query(None, description="Filter by repository name"),
    db: Session = Depends(get_db)
):
    """Get statistics for users' GitHub activity"""
    try:
        # Create a query to group by username
        query = db.query(
            GitHubData.username,
            func.count(GitHubData.id).label("total_pull_requests"),
            func.sum(GitHubData.total_commits).label("total_commits"),
            (func.sum(GitHubData.passing_commits) / func.sum(GitHubData.total_commits)).label("passing_commits_ratio"),
            func.avg(GitHubData.changes_per_commit).label("avg_changes_per_commit"),
            func.sum(
                GitHubData.approved_reviews_given + 
                GitHubData.changes_requested_reviews_given + 
                GitHubData.commented_reviews_given
            ).label("reviews_given"),
            func.sum(
                GitHubData.approved_reviews_received + 
                GitHubData.changes_requested_reviews_received + 
                GitHubData.commented_reviews_received
            ).label("reviews_received")
        ).group_by(GitHubData.username)
        
        # Apply filters if provided
        if org_name:
            query = query.filter(GitHubData.org_name == org_name)
        
        if repository_name:
            query = query.filter(GitHubData.repository_name == repository_name)
        
        # Execute the query
        results = query.all()
        
        # Convert query results to response model
        stats_list = []
        for row in results:
            # Handle division by zero for passing_commits_ratio
            passing_ratio = row.passing_commits_ratio if row.passing_commits_ratio is not None else 0.0
            
            stats = UserStats(
                username=row.username,
                total_pull_requests=row.total_pull_requests,
                total_commits=row.total_commits,
                passing_commits_ratio=passing_ratio,
                avg_changes_per_commit=row.avg_changes_per_commit,
                reviews_given=row.reviews_given,
                reviews_received=row.reviews_received
            )
            stats_list.append(stats)
        
        logger.info(f"Successfully generated stats for {len(stats_list)} users")
        return stats_list
    
    except Exception as e:
        logger.error(f"Error generating user stats: {str(e)}", exc_info=True)
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
            "/pull-requests": "Get GitHub pull request data with various filtering options",
            "/repositories": "Get a list of all unique repository names",
            "/organizations": "Get a list of all unique organization names",
            "/users": "Get a list of all unique usernames with optional filtering",
            "/repository-summary": "Get summary statistics for repositories",
            "/user-stats": "Get statistics for users' GitHub activity",
            "/health": "Check API health status"
        }
    }

if __name__ == "__main__":
    # This will only be used when running the file directly, not when mounted in server.py
    uvicorn.run("app.github.main:app", host="0.0.0.0", port=8000, reload=True)