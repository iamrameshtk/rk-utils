# SonarQube Analysis API

A FastAPI microservice that retrieves SonarQube static analysis data from a PostgreSQL database.

## Features

- Retrieve SonarQube analysis reports with pagination and sorting
- Filter reports by repository key/project
- Get a list of all available projects

## Installation

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and update with your database credentials
6. Create database tables: `python scripts/create_tables.py`
7. (Optional) Add sample data: `python scripts/seed_data.py`

## Running the API

```bash
python run.py
```

## Additional Information:

- The API will be available at http://localhost:8000

Documentation is available at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

API Endpoints

- GET /reports/ - Get paginated and sorted reports

    Query parameters:

    - repository_key - Filter by repository key/project
    - page - Page number (default: 1)
    - page_size - Items per page (default: 10)
    - sort_by - Field to sort by (default: "timestamp")
    - sort_order - Sort order "asc" or "desc" (default: "desc")

- GET /reports/{report_id} - Get a specific report by ID
- GET /reports/projects/ - Get a list of all unique projects

## Running Tests

```bash
pytest
```

API Code with a well-organized, production-ready FastAPI application for SonarQube data.
Users can customize the implementation as needed while maintaining this clean structure.