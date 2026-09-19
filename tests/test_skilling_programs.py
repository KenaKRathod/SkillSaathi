import os
import csv
from unittest.mock import patch
from bs4 import BeautifulSoup
from scripts.build_skilling_programs import parse_row, main, scrape_programs

def test_parse_row():
    html = """
    <div class="course-card">
        <h3 class="course-title">Retail Sales Associate</h3>
        <span class="scheme-name">PMKVY 4.0</span>
        <span class="sector-name">Retail</span>
        <span class="nsqf-level">4</span>
        <span class="duration">300 Hours</span>
        <span class="cost">Free</span>
    </div>
    """
    soup = BeautifulSoup(html, "html.parser")
    row = soup.find("div", class_="course-card")
    parsed = parse_row(row)
    
    assert parsed["name"] == "Retail Sales Associate"
    assert parsed["scheme"] == "PMKVY 4.0"
    assert parsed["sector"] == "Retail"
    assert parsed["nsqf_level"] == "4"
    assert parsed["duration"] == "300 Hours"
    assert parsed["cost"] == "Free"
    assert parsed["data_confidence"] == "scraped"
    assert parsed["source_url"] != ""

@patch("scripts.build_skilling_programs.scrape_programs")
def test_csv_output_and_partial_confidence(mock_scrape):
    # Mock a successful scrape returning 15 rows
    programs = []
    for i in range(15):
        programs.append({
            'name': f'Course {i}',
            'scheme': 'PMKVY 4.0',
            'sector': 'IT',
            'nsqf_level': '4' if i < 10 else '', # Some missing to trigger partial
            'duration': '300 Hours',
            'cost': 'Free',
            'district_availability': '',
            'min_age': '',
            'max_age': '',
            'min_education': '',
            'wage_outcome': '',
            'source_url': 'https://www.skillindiadigital.gov.in/sector/list?forCourse=true',
            'data_confidence': 'scraped'
        })
    mock_scrape.return_value = programs
    
    # Run main
    if os.path.exists("data/skilling_programs.csv"):
        os.remove("data/skilling_programs.csv")
    main()
    
    assert os.path.exists("data/skilling_programs.csv")
    
    # Read CSV and verify
    with open("data/skilling_programs.csv", "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        
        assert len(reader) == 15
        for row in reader:
            assert row["name"] != ""
            assert row["scheme"] != ""
            assert row["sector"] != ""
            assert row["source_url"] != ""
            
            if row["name"] == "Course 11":
                assert row["data_confidence"] == "partial"
                assert "PMKVY-4.0-Guidelines_final-copy.pdf" in row["source_url"]

@patch("scripts.build_skilling_programs.scrape_programs")
def test_fallback_manual_entry(mock_scrape):
    # Mock scrape returning 5 rows
    mock_scrape.return_value = [{"name": "Course"} for _ in range(5)]
    
    if os.path.exists("manual_entry_needed.md"):
        os.remove("manual_entry_needed.md")
        
    main()
    
    assert os.path.exists("manual_entry_needed.md")
    with open("manual_entry_needed.md", "r", encoding="utf-8") as f:
        content = f.read()
        assert "Manual Entry Needed" in content
