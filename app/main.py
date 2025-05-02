from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints import reports
from app.config import API_TITLE, API_DESCRIPTION, API_VERSION

# Create FastAPI app
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(reports.router)

@app.get("/", tags=["root"])
def read_root():
    return {
        "message": "Welcome to the SonarQube Analysis API",
        "docs": "/docs"
    }