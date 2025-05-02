from sqlalchemy.orm import Session
from app.models.sonarqube import SonarQubeReport
from typing import List, Optional, Dict, Any

def get_paginated_reports(
    db: Session,
    repository_key: Optional[str] = None, 
    page: int = 1,
    page_size: int = 10,
    sort_column = None,
    sort_order: str = "desc"
) -> Dict[str, Any]:
    """
    Get paginated and sorted reports with optional filtering
    """
    # Build query
    query = db.query(SonarQubeReport)
    
    # Apply repository_key filter if provided
    if repository_key:
        query = query.filter(SonarQubeReport.repository_key == repository_key)
    
    # Get total count for pagination
    total_items = query.count()
    
    # Apply sorting
    if sort_column:
        if sort_order == "desc":
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

def get_report_by_id(db: Session, report_id: int):
    """
    Get a single report by ID
    """
    return db.query(SonarQubeReport).filter(SonarQubeReport.id == report_id).first()

def get_unique_projects(db: Session) -> List[str]:
    """
    Get a list of all unique project/repository keys
    """
    projects = db.query(SonarQubeReport.repository_key).distinct().all()
    return [project[0] for project in projects]