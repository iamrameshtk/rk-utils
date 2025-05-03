# server.py
import os
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import uvicorn

# Import both APIs
from app.sonarqube.main import app as sonarqube_app
from app.github.main import app as github_app

# Import models and session dependencies for integrated endpoints
from app.sonarqube.main import SonarQubeReport, get_db as get_sonarqube_db
from app.github.main import GitHubData, get_db as get_github_db

# Setup shared logger
from shared.logging import setup_logger
logger = setup_logger("integrated_api")

# Initialize the main FastAPI app
app = FastAPI(
    title="DevOps Metrics API",
    description="Integrated API for DevOps metrics from SonarQube and GitHub",
    version="1.0.0"
)

# Mount the individual APIs under their respective prefixes
app.mount("/sonarqube", sonarqube_app)
app.mount("/github", github_app)

# Model for combined repository metrics
class RepositoryHealthMetrics(BaseModel):
    repository_name: str
    code_quality_metrics: dict
    github_metrics: dict
    combined_health_score: float
    last_updated: datetime
    
    class Config:
        orm_mode = True

# Create a router for integrated endpoints
from fastapi import APIRouter
integrated_router = APIRouter(prefix="/integrated", tags=["Integrated Metrics"])

@integrated_router.get("/repository-health", response_model=List[RepositoryHealthMetrics])
def get_repository_health(
    org_name: Optional[str] = Query(None, description="Filter by organization name"),
    days: int = Query(30, description="Number of days to analyze"),
    sonarqube_db: Session = Depends(get_sonarqube_db),
    github_db: Session = Depends(get_github_db)
):
    """
    Get combined health metrics for repositories by integrating SonarQube and GitHub data
    """
    try:
        logger.info(f"Generating integrated repository health metrics for org_name={org_name}, days={days}")
        
        # Calculate the date threshold
        date_threshold = datetime.utcnow() - timedelta(days=days)
        
        # Get SonarQube data
        sonarqube_query = sonarqube_db.query(SonarQubeReport)\
            .filter(SonarQubeReport.timestamp >= date_threshold)
        
        # Get GitHub data
        github_query = github_db.query(GitHubData)\
            .filter(GitHubData.created_at >= date_threshold)
        
        # Apply organization filter if provided
        if org_name:
            github_query = github_query.filter(GitHubData.org_name == org_name)
            # For SonarQube, assuming repository_key has org name as prefix or in team field
            sonarqube_query = sonarqube_query.filter(
                SonarQubeReport.team == org_name
            )
        
        # Execute queries
        sonarqube_data = sonarqube_query.all()
        github_data = github_query.all()
        
        logger.info(f"Retrieved {len(sonarqube_data)} SonarQube reports and {len(github_data)} GitHub PRs")
        
        # Group data by repository
        sonar_by_repo = {}
        for report in sonarqube_data:
            repo_key = report.repository_key
            if repo_key not in sonar_by_repo:
                sonar_by_repo[repo_key] = []
            sonar_by_repo[repo_key].append(report)
        
        github_by_repo = {}
        for pr_data in github_data:
            repo_name = pr_data.repository_name
            if repo_name not in github_by_repo:
                github_by_repo[repo_name] = []
            github_by_repo[repo_name].append(pr_data)
        
        # Find common repositories and create combined metrics
        result = []
        for repo_key, sonar_reports in sonar_by_repo.items():
            # Extract repository name from SonarQube key (assuming format like "org/repo")
            repo_parts = repo_key.split('/')
            repo_name = repo_parts[-1] if len(repo_parts) > 1 else repo_key
            
            if repo_name in github_by_repo:
                github_prs = github_by_repo[repo_name]
                
                # Calculate SonarQube metrics
                latest_report = max(sonar_reports, key=lambda x: x.timestamp)
                avg_code_smells = sum(r.code_smells for r in sonar_reports) / len(sonar_reports)
                avg_tech_debt = sum(r.technical_debt_minutes for r in sonar_reports) / len(sonar_reports)
                
                # Calculate GitHub metrics
                total_prs = len(github_prs)
                passing_commit_ratio = sum(pr.passing_commits for pr in github_prs) / sum(pr.total_commits for pr in github_prs) if sum(pr.total_commits for pr in github_prs) > 0 else 0
                avg_changes = sum(pr.changes_per_commit for pr in github_prs) / len(github_prs)
                
                # Calculate a combined health score (this is a simple example)
                # Higher score is better (1.0 is perfect)
                code_quality_factor = max(0, 1 - (avg_code_smells / 100) - (avg_tech_debt / 1000))
                github_factor = max(0, passing_commit_ratio)
                combined_score = (code_quality_factor + github_factor) / 2
                
                # Create the response model
                health_metrics = RepositoryHealthMetrics(
                    repository_name=repo_name,
                    code_quality_metrics={
                        "latest_code_smells": latest_report.code_smells,
                        "latest_tech_debt_minutes": latest_report.technical_debt_minutes,
                        "latest_security_hotspots": latest_report.security_hotspots,
                        "security_rating": latest_report.security_rating,
                        "avg_code_smells": avg_code_smells,
                        "avg_tech_debt_minutes": avg_tech_debt
                    },
                    github_metrics={
                        "pull_request_count": total_prs,
                        "passing_commit_ratio": passing_commit_ratio,
                        "avg_changes_per_commit": avg_changes
                    },
                    combined_health_score=combined_score,
                    last_updated=datetime.utcnow()
                )
                
                result.append(health_metrics)
        
        logger.info(f"Generated health metrics for {len(result)} repositories")
        return result
    
    except Exception as e:
        logger.error(f"Error generating combined metrics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating combined metrics: {str(e)}")

# Add the integrated router to the main app
app.include_router(integrated_router)

@app.get("/")
def root():
    """Root endpoint to provide API information"""
    return {
        "name": "DevOps Metrics API",
        "version": "1.0.0",
        "services": {
            "sonarqube": {
                "description": "SonarQube metrics and reports",
                "endpoint": "/sonarqube"
            },
            "github": {
                "description": "GitHub pull request and repository metrics",
                "endpoint": "/github"
            },
            "integrated": {
                "description": "Combined metrics from multiple data sources",
                "endpoint": "/integrated"
            }
        }
    }

@app.get("/health")
def health_check():
    """Check the health of all services"""
    try:
        # Check SonarQube API health
        sonarqube_health = sonarqube_app.url_path_for("health_check")
        
        # Check GitHub API health
        github_health = github_app.url_path_for("health_check")
        
        return {
            "status": "healthy",
            "services": {
                "sonarqube": {"status": "connected", "endpoint": sonarqube_health},
                "github": {"status": "connected", "endpoint": github_health}
            }
        }
    except Exception as e:
        logger.error(f"Main API health check failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=503, detail="Service unhealthy")

if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.getenv("PORT", "8000"))
    
    # Run the server
    logger.info(f"Starting integrated DevOps Metrics API server on port {port}")
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)