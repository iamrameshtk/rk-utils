from sqlalchemy import Column, Integer, String, Float, DateTime
from app.database import Base

class SonarQubeReport(Base):
    __tablename__ = "sonarqube_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    repository_key = Column(String, nullable=False, index=True)
    code_smells = Column(Integer)
    technical_debt_minutes = Column(Float)
    security_hotspots = Column(Integer)
    security_rating = Column(String)