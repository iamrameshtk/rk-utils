# server.py
import os
from fastapi import FastAPI, APIRouter
from fastapi.responses import RedirectResponse
from fastapi.openapi.utils import get_openapi
import uvicorn

# Import both APIs
from app.sonarqube.main import app as sonarqube_app
from app.github.main import app as github_app

# Import routers from each API to include them directly in the main app's OpenAPI docs
from app.sonarqube.main import router as sonarqube_router
from app.github.main import router as github_router

# Setup shared logger
from shared.logging import setup_logger
logger = setup_logger("api_server")

# Initialize the main FastAPI app
app = FastAPI(
    title="DevOps Metrics API",
    description="Combined API for DevOps metrics from SonarQube and GitHub",
    version="1.0.0"
)

# Include the routers directly in the main app with prefixes
# This makes them show up in the Swagger UI
app.include_router(
    sonarqube_router,
    prefix="/sonarqube",
    tags=["SonarQube"]
)

app.include_router(
    github_router,
    prefix="/github",
    tags=["GitHub"]
)

# Still mount the original apps for backward compatibility
# Note: These won't appear in the Swagger UI documentation
app.mount("/sonarqube-app", sonarqube_app)
app.mount("/github-app", github_app)

@app.get("/", include_in_schema=False)
def root():
    """Root endpoint redirects to docs"""
    return RedirectResponse(url="/docs")

@app.get("/api-info", tags=["General"])
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

@app.get("/health", tags=["General"])
def health_check():
    """Check the health of all services"""
    # This is a simplified health check that doesn't actually call the 
    # individual services but just reports the API gateway status
    return {
        "status": "healthy",
        "message": "API gateway is running. Check individual service health at their respective endpoints."
    }

# Custom OpenAPI to ensure proper documentation
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="DevOps Metrics API",
        version="1.0.0",
        description="Combined API for SonarQube and GitHub metrics with comprehensive filtering capabilities",
        routes=app.routes,
    )
    
    # Add custom documentation details if needed
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.getenv("PORT", "8000"))
    
    # Run the server
    logger.info(f"Starting DevOps Metrics API server on port {port}")
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)