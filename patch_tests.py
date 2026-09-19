with open('tests/test_recommend.py', 'a') as f:
    f.write('''
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
''')
