# server.py
import os
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
import uvicorn

# Import both APIs
from app.sonarqube.main import app as sonarqube_app
from app.github.main import app as github_app

# Setup shared logger
from shared.logging import setup_logger
logger = setup_logger("api_server")

# Initialize the main FastAPI app
app = FastAPI(
    title="DevOps Metrics API",
    description="Combined API for DevOps metrics from SonarQube and GitHub",
    version="1.0.0"
)

# Mount the individual APIs under their respective prefixes
app.mount("/sonarqube", sonarqube_app)
app.mount("/github", github_app)

@app.get("/", include_in_schema=False)
def root():
    """Root endpoint redirects to docs"""
    return RedirectResponse(url="/docs")

@app.get("/api-info")
def api_info():
    """Provides information about the available APIs"""
    return {
        "name": "DevOps Metrics API",
        "version": "1.0.0",
        "services": {
            "sonarqube": {
                "description": "SonarQube metrics and reports",
                "endpoint": "/sonarqube",
                "health_check": "/sonarqube/health"
            },
            "github": {
                "description": "GitHub pull request and repository metrics",
                "endpoint": "/github",
                "health_check": "/github/health"
            }
        }
    }

@app.get("/health")
def health_check():
    """Check the health of all services"""
    # This is a simplified health check that doesn't actually call the 
    # individual services but just reports the API gateway status
    return {
        "status": "healthy",
        "message": "API gateway is running. Check individual service health at their respective endpoints."
    }

if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.getenv("PORT", "8000"))
    
    # Run the server
    logger.info(f"Starting DevOps Metrics API server on port {port}")
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)