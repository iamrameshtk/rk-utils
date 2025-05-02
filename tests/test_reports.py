def test_get_reports(client):
    response = client.get("/reports/")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 2
    assert data["total"] == 2
    assert data["page"] == 1

def test_get_reports_with_pagination(client):
    response = client.get("/reports/?page=1&page_size=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["total"] == 2
    assert data["page"] == 1
    assert data["has_next"] == True

def test_get_reports_with_sort(client):
    # Test ascending sort
    response = client.get("/reports/?sort_by=code_smells&sort_order=asc")
    assert response.status_code == 200
    data = response.json()
    assert data["items"][0]["code_smells"] == 85  # Lowest code smells

    # Test descending sort
    response = client.get("/reports/?sort_by=code_smells&sort_order=desc")
    assert response.status_code == 200
    data = response.json()
    assert data["items"][0]["code_smells"] == 120  # Highest code smells

def test_get_reports_with_filter(client):
    response = client.get("/reports/?repository_key=project-a")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["repository_key"] == "project-a"

def test_get_report_by_id(client):
    # First get all reports to find an ID
    response = client.get("/reports/")
    data = response.json()
    report_id = data["items"][0]["id"]
    
    # Now get specific report
    response = client.get(f"/reports/{report_id}")
    assert response.status_code == 200
    report = response.json()
    assert report["id"] == report_id

def test_get_report_by_id_not_found(client):
    response = client.get("/reports/9999")  # Non-existent ID
    assert response.status_code == 404

def test_get_projects(client):
    response = client.get("/reports/projects/")
    assert response.status_code == 200
    projects = response.json()
    assert len(projects) == 2
    assert "project-a" in projects
    assert "project-b" in projects