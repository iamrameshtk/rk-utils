from datetime import datetime
from app.database import SessionLocal
from app.models.sonarqube import SonarQubeReport

def seed_data():
    db = SessionLocal()
    
    try:
        # Check if data already exists
        existing_count = db.query(SonarQubeReport).count()
        if existing_count > 0:
            print(f"Database already contains {existing_count} records. Skipping seed.")
            return
        
        # Sample data
        sample_reports = [
            SonarQubeReport(
                timestamp=datetime(2025, 4, 1, 10, 30),
                repository_key="project-a",
                code_smells=120,
                technical_debt_minutes=450.5,
                security_hotspots=8,
                security_rating="A"
            ),
            SonarQubeReport(
                timestamp=datetime(2025, 4, 2, 14, 15),
                repository_key="project-b",
                code_smells=85,
                technical_debt_minutes=310.2,
                security_hotspots=3,
                security_rating="B"
            ),
            SonarQubeReport(
                timestamp=datetime(2025, 4, 3, 9, 45),
                repository_key="project-a",
                code_smells=110,
                technical_debt_minutes=420.0,
                security_hotspots=6,
                security_rating="A"
            ),
            SonarQubeReport(
                timestamp=datetime(2025, 4, 4, 16, 20),
                repository_key="project-c",
                code_smells=210,
                technical_debt_minutes=780.5,
                security_hotspots=12,
                security_rating="C"
            ),
            SonarQubeReport(
                timestamp=datetime(2025, 4, 5, 11, 10),
                repository_key="project-b",
                code_smells=80,
                technical_debt_minutes=290.8,
                security_hotspots=2,
                security_rating="A"
            ),
        ]
        
        db.add_all(sample_reports)
        db.commit()
        
        print(f"Added {len(sample_reports)} sample reports to the database.")
    
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()