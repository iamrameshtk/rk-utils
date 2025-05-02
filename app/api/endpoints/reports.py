from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.sonarqube import SonarQubeReport
from app.schemas.sonarqube import SonarQubeReportResponse, PaginatedResponse
from app.api.dependencies import validate_sort_parameters

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/", response_model=PaginatedResponse)
def get_reports(
    db: Session = Depends(get_db),
    repository_key: Optional[str] = Query(None, description="Filter by repository key/project"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    sort_params: dict = Depends(validate_sort_parameters)
):
    # Build query
    query = db.query(SonarQubeReport)
    
    # Apply repository_key filter if provided
    if repository_key:
        query = query.filter(SonarQubeReport.repository_key == repository_key)
    
    # Get total count for pagination
    total_items = query.count()
    
    # Apply sorting
    sort_column = sort_params["sort_column"]
    if sort_params["sort_order"] == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # Apply pagination
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    
    # Calculate pagination metadata
    total_pages = (total_items + page_size - 1) // page_size
    
    return {
        "items": items,
        "total": total_items,
        "page": page,
        "page_size": page_size,
        "pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }

@router.get("/{report_id}", response_model=SonarQubeReportResponse)
def get_report_by_id(report_id: int, db: Session = Depends(get_db)):
    report = db.query(SonarQubeReport).filter(SonarQubeReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

@router.get("/projects/", response_model=List[str])
def get_projects(db: Session = Depends(get_db)):
    """Get a list of all unique project/repository keys"""
    projects = db.query(SonarQubeReport.repository_key).distinct().all()
    return [project[0] for project in projects]