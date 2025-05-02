from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class SonarQubeReportBase(BaseModel):
    timestamp: datetime
    repository_key: str
    code_smells: int
    technical_debt_minutes: float
    security_hotspots: int
    security_rating: str

class SonarQubeReportResponse(SonarQubeReportBase):
    id: int
    
    class Config:
        orm_mode = True

class PaginatedResponse(BaseModel):
    items: List[SonarQubeReportResponse]
    total: int
    page: int
    page_size: int
    pages: int
    has_next: bool
    has_prev: bool