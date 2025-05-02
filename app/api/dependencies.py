from fastapi import Query, HTTPException
from typing import Dict, Any
from app.models.sonarqube import SonarQubeReport

# Valid sorting fields to prevent SQL injection
VALID_SORT_FIELDS = {
    "timestamp": SonarQubeReport.timestamp,
    "repository_key": SonarQubeReport.repository_key,
    "code_smells": SonarQubeReport.code_smells,
    "technical_debt_minutes": SonarQubeReport.technical_debt_minutes,
    "security_hotspots": SonarQubeReport.security_hotspots,
    "security_rating": SonarQubeReport.security_rating
}

def validate_sort_parameters(
    sort_by: str = Query("timestamp", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order (asc or desc)")
) -> Dict[str, Any]:
    # Validate sort field
    if sort_by not in VALID_SORT_FIELDS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort field. Valid options are: {', '.join(VALID_SORT_FIELDS.keys())}"
        )
    
    # Validate sort order
    if sort_order not in ["asc", "desc"]:
        raise HTTPException(
            status_code=400,
            detail="Sort order must be 'asc' or 'desc'"
        )
    
    return {
        "sort_column": VALID_SORT_FIELDS[sort_by],
        "sort_order": sort_order
    }