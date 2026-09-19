import pandas as pd
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

client = TestClient(app)

mock_programs_data = [
    {
        "name": "General Course",
        "scheme": "PMKVY 4.0",
        "sector": "General",
        "nsqf_level": "3",
        "duration": "100 Hours",
        "cost": "Free",
        "district_availability": "mumbai",
        "min_age": "18",
        "max_age": "30",
        "min_education": "10th",
        "wage_outcome": "10000",
        "source_url": "http://example.com",
        "data_confidence": "scraped"
    },
    {
        "name": "IT Advanced Course",
        "scheme": "PMKVY 4.0",
        "sector": "IT",
        "nsqf_level": "5",
        "duration": "200 Hours",
        "cost": "Free",
        "district_availability": "pune",
        "min_age": "20",
        "max_age": "40",
        "min_education": "12th",
        "wage_outcome": "25000",
        "source_url": "http://example.com",
        "data_confidence": "scraped"
    },
    {
        "name": "Retail Sales Associate",
        "scheme": "PMKVY 4.0",
        "sector": "Retail",
        "nsqf_level": "4",
        "duration": "300 Hours",
        "cost": "Free",
        "district_availability": "mumbai",
        "min_age": "18",
        "max_age": "35",
        "min_education": "10th",
        "wage_outcome": "15000",
        "source_url": "http://example.com",
        "data_confidence": "scraped"
    },
    {
        "name": "Plumbing Basics",
        "scheme": "PMKVY 4.0",
        "sector": "Construction",
        "nsqf_level": "3",
        "duration": "150 Hours",
        "cost": "Free",
        "district_availability": "mumbai",
        "min_age": "18",
        "max_age": "50",
        "min_education": "8th",
        "wage_outcome": "12000",
        "source_url": "http://example.com",
        "data_confidence": "scraped"
    }
]

mock_df = pd.DataFrame(mock_programs_data)
mock_df.fillna('', inplace=True)

@patch("app.main.PROGRAMS_DF", mock_df)
def test_recommend_returns_eligible_program_in_top_3():
    # Profile that explicitly matches Retail Sales Associate
    req_body = {
        "mapped_categories": {
            "primary_category": "Retail",
            "secondary_category": ""
        },
        "profile": {
            "age": "25",
            "district": "mumbai",
            "education": "10th",
            "wage_goal": "14000"
        }
    }
    
    response = client.post("/recommend", json=req_body)
    assert response.status_code == 200
    data = response.json()
    
    # Check that we got at most 3 rows
    assert len(data["results"]) <= 3
    
    # "Retail Sales Associate" should be the top match
    names = [row["name"] for row in data["results"]]
    assert "Retail Sales Associate" in names
    
    # Age filter test: Plumbing Basics also available in mumbai for 25 yr old
    # But IT Advanced Course is in pune, so it should be filtered out
    assert "IT Advanced Course" not in names

@patch("app.main.PROGRAMS_DF", mock_df)
def test_recommend_scoring():
    # Compare "Retail Sales Associate" vs "General Course" for a Retail profile
    req_body = {
        "mapped_categories": {
            "primary_category": "Retail",
            "secondary_category": ""
        },
        "profile": {
            "age": "20",
            "district": "mumbai",
            "education": "10th",
            "wage_goal": "10000"
        }
    }
    
    response = client.post("/recommend", json=req_body)
    assert response.status_code == 200
    data = response.json()
    
    # Extract scores
    retail_score = next(row["score"] for row in data["results"] if row["name"] == "Retail Sales Associate")
    general_score = next(row["score"] for row in data["results"] if row["name"] == "General Course")
    
    # A program with perfect category match + eligibility scores higher than one with neither
    # Retail matches category (0.5), General does not (0.0)
    assert retail_score > general_score

from unittest.mock import MagicMock

@patch("app.main.PROGRAMS_DF", mock_df)
@patch("app.main.genai.Client")
def test_recommend_reasoning_success(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.text = "This is a great program for you."
    mock_client.models.generate_content.return_value = mock_response

    req_body = {
        "mapped_categories": {"primary_category": "Retail"},
        "profile": {"age": "25", "district": "mumbai"}
    }
    response = client.post("/recommend", json=req_body)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) > 0
    assert data["results"][0]["reasoning"] == "This is a great program for you."

@patch("app.main.PROGRAMS_DF", mock_df)
@patch("app.main.genai.Client")
def test_recommend_reasoning_fallback(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_client.models.generate_content.side_effect = Exception("LLM Error")

    req_body = {
        "mapped_categories": {"primary_category": "Retail"},
        "profile": {"age": "25", "district": "mumbai", "sector": "Sales"}
    }
    response = client.post("/recommend", json=req_body)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) > 0
    reasoning = data["results"][0]["reasoning"]
    
    assert "is a" in reasoning
    assert "program matching your" in reasoning

@patch("app.main.PROGRAMS_DF", mock_df)
@patch("app.main.genai.Client")
def test_recommend_relaxed_filters(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_client.models.generate_content.return_value = MagicMock(text="Reasoning")

    # Match zero programs normally (age 99, district kolkata)
    req_body = {
        "mapped_categories": {"primary_category": "Retail"},
        "profile": {"age": "99", "district": "kolkata"}
    }
    response = client.post("/recommend", json=req_body)
    assert response.status_code == 200
    data = response.json()
    
    # Should have results because filters were relaxed
    assert "results" in data
    assert len(data["results"]) > 0
    assert "relaxed_filters" in data
    assert "district_availability" in data["relaxed_filters"]
    assert "age_range" in data["relaxed_filters"]
